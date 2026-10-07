//+------------------------------------------------------------------+
//| RSI2_Nasdaq.mq5                                                   |
//| Compra el Nasdaq tras una caída (RSI de 2 días) en tendencia      |
//| alcista y vende cuando vuelve a su media de 5 días.               |
//|                                                                   |
//| Reglas (las mismas del backtest scripts/rsi2_diario.py):          |
//|  - "Cierre del día" = precio a las 15:55 de Nueva York.           |
//|  - Compra si RSI(2) < Umbral y cierre > media de 200 días.        |
//|  - Vende si cierre > media de 5 días o tras MaxDias días.         |
//|  - Stop de emergencia opcional en puntos (0 = sin stop).          |
//| Pensado para USTECm (contrato 1): 0,20 lotes por cada 1.000 $.     |
//| Probar SIEMPRE primero en cuenta demo.                            |
//+------------------------------------------------------------------+
#property copyright "BotScalping"
#property version   "1.00"
#property strict

#include <Trade/Trade.mqh>

input double Lotes        = 0.20;   // lote fijo (USTECm: 0,20 por cada 1.000 $)
input double Umbral       = 20.0;   // RSI(2) por debajo de este valor = caída
input int    MediaLarga   = 200;    // filtro de tendencia (días)
input int    MediaCorta   = 5;      // salida al cerrar sobre esta media (días)
input int    MaxDias      = 10;     // salida forzada tras N días
input double StopPuntos   = 0;      // stop de emergencia en puntos del índice (0 = sin stop)
input int    HoraNY       = 15;     // hora de Nueva York a la que se evalúa
input int    MinutoNY     = 55;
input int    OffsetServidorUTC = 0; // horas que el servidor va por delante de UTC (Exness = 0)
input long   Magic        = 202610;

CTrade trade;
int    ultimoDiaEvaluado = -1;

//--- ¿horario de verano en EE. UU.? (2º domingo de marzo 2:00 -> 1er domingo de noviembre 2:00, hora local)
int NthSunday(int year, int mon, int n)
{
   MqlDateTime t; t.year = year; t.mon = mon; t.day = 1; t.hour = 0; t.min = 0; t.sec = 0;
   datetime d = StructToTime(t); TimeToStruct(d, t);
   int first = 1 + (7 - t.day_of_week) % 7;
   return first + 7 * (n - 1);
}
bool UsDst(datetime utc)
{
   MqlDateTime t; TimeToStruct(utc, t);
   MqlDateTime a; a.year = t.year; a.mon = 3;  a.day = NthSunday(t.year, 3, 2);  a.hour = 7; a.min = 0; a.sec = 0; // 2:00 EST = 7:00 UTC
   MqlDateTime b; b.year = t.year; b.mon = 11; b.day = NthSunday(t.year, 11, 1); b.hour = 6; b.min = 0; b.sec = 0; // 2:00 EDT = 6:00 UTC
   return utc >= StructToTime(a) && utc < StructToTime(b);
}
datetime ServerToUtc(datetime s) { return s - OffsetServidorUTC * 3600; }
datetime UtcToServer(datetime u) { return u + OffsetServidorUTC * 3600; }
datetime UtcToNy(datetime u)     { return u - (UsDst(u) ? 4 : 5) * 3600; }
datetime NyToUtc(datetime ny)    { datetime u = ny + 5 * 3600; return UsDst(u - 3600) ? ny + 4 * 3600 : u; }

//--- precio a las HoraNY:MinutoNY de un día de Nueva York (cierre de la vela M5 que empieza 5 min antes)
bool CloseAtNy(int y, int m, int d, double &px)
{
   MqlDateTime t; t.year = y; t.mon = m; t.day = d; t.hour = HoraNY; t.min = MinutoNY; t.sec = 0;
   datetime srv = UtcToServer(NyToUtc(StructToTime(t))) - 5 * 60;
   int sh = iBarShift(_Symbol, PERIOD_M5, srv, false);
   if(sh < 0) return false;
   datetime bt = iTime(_Symbol, PERIOD_M5, sh);
   if(srv - bt > 30 * 60) return false;       // no hubo mercado ese día (festivo)
   px = iClose(_Symbol, PERIOD_M5, sh);
   return px > 0;
}

//--- cierres diarios de NY, del más antiguo al más reciente; el último es hoy (precio actual)
int DailyCloses(int need, double &out[])
{
   double tmp[]; ArrayResize(tmp, 0);
   datetime nyNow = UtcToNy(ServerToUtc(TimeCurrent()));
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   ArrayResize(tmp, 1); tmp[0] = bid;
   for(int k = 1; k < need * 2 && ArraySize(tmp) < need; k++)
   {
      MqlDateTime t; TimeToStruct(nyNow - k * 86400, t);
      if(t.day_of_week == 0 || t.day_of_week == 6) continue;
      double px;
      if(CloseAtNy(t.year, t.mon, t.day, px)) { int n = ArraySize(tmp); ArrayResize(tmp, n + 1); tmp[n] = px; }
   }
   int n = ArraySize(tmp); ArrayResize(out, n);
   for(int i = 0; i < n; i++) out[i] = tmp[n - 1 - i];
   return n;
}

double Sma(const double &c[], int len)
{
   int n = ArraySize(c); if(n < len) return 0;
   double s = 0; for(int i = n - len; i < n; i++) s += c[i];
   return s / len;
}

double Rsi2(const double &c[])
{
   double up = 0, dn = 0; int n = ArraySize(c);
   for(int i = 1; i < n; i++)
   {
      double d = c[i] - c[i - 1];
      up = 0.5 * up + 0.5 * MathMax(d, 0);   // suavizado de Wilder con periodo 2 (alfa 1/2)
      dn = 0.5 * dn + 0.5 * MathMax(-d, 0);
   }
   if(dn == 0) return 100;
   return 100 - 100 / (1 + up / dn);
}

bool MiPosicion(ulong &ticket, datetime &abierta)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong tk = PositionGetTicket(i);
      if(PositionSelectByTicket(tk) && PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == Magic)
      { ticket = tk; abierta = (datetime)PositionGetInteger(POSITION_TIME); return true; }
   }
   return false;
}

int DiasHabiles(datetime desde, datetime hasta)
{
   int n = 0;
   for(datetime d = desde + 86400; d <= hasta; d += 86400)
   { MqlDateTime t; TimeToStruct(d, t); if(t.day_of_week != 0 && t.day_of_week != 6) n++; }
   return n;
}

int OnInit()
{
   trade.SetExpertMagicNumber(Magic);
   EventSetTimer(30);
   Print("RSI2_Nasdaq listo en ", _Symbol, ". Evalúa a las ", HoraNY, ":", MinutoNY, " de Nueva York.");
   return INIT_SUCCEEDED;
}
void OnDeinit(const int reason) { EventKillTimer(); }

void OnTimer()
{
   datetime nyNow = UtcToNy(ServerToUtc(TimeCurrent()));
   MqlDateTime t; TimeToStruct(nyNow, t);
   if(t.day_of_week == 0 || t.day_of_week == 6) return;
   if(t.hour != HoraNY || t.min < MinutoNY) return;
   if(t.day_of_year == ultimoDiaEvaluado) return;
   ultimoDiaEvaluado = t.day_of_year;

   double c[];
   int n = DailyCloses(MediaLarga + 60, c);
   if(n < MediaLarga + 10) { Print("Historial insuficiente: ", n, " días. Abre un gráfico M5 y deja que descargue más historial."); return; }
   double cierre = c[n - 1], rsi = Rsi2(c), ma200 = Sma(c, MediaLarga), ma5 = Sma(c, MediaCorta);
   PrintFormat("%04d-%02d-%02d NY | cierre %.2f | RSI2 %.1f | media%d %.2f | media%d %.2f", t.year, t.mon, t.day, cierre, rsi, MediaLarga, ma200, MediaCorta, ma5);

   ulong tk; datetime abierta;
   if(MiPosicion(tk, abierta))
   {
      int dias = DiasHabiles(UtcToNy(ServerToUtc(abierta)), nyNow);
      if(cierre > ma5 || dias >= MaxDias)
      {
         if(trade.PositionClose(tk)) PrintFormat("Cerrada: cierre %.2f > media5 %.2f o %d días", cierre, ma5, dias);
         else Print("Error al cerrar: ", trade.ResultRetcodeDescription());
      }
      return;
   }
   if(rsi < Umbral && cierre > ma200)
   {
      double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double sl = StopPuntos > 0 ? NormalizeDouble(ask - StopPuntos, _Digits) : 0;
      if(trade.Buy(Lotes, _Symbol, ask, sl, 0, "RSI2")) PrintFormat("Compra %.2f lotes a %.2f (RSI2 %.1f)", Lotes, ask, rsi);
      else Print("Error al comprar: ", trade.ResultRetcodeDescription());
   }
}
