//+------------------------------------------------------------------+
//| Estructura_Oro.mq5                                                |
//| Opera a favor de la estructura de 1 h y 4 h en el oro, entrando   |
//| en el retroceso de 5 min. Reglas del backtest                     |
//| scripts/estructura_ajustes.py ("máx 2 por dirección"):            |
//|  - Tendencia: en H1 y en H4, los dos últimos máximos y mínimos    |
//|    (fractal de 3 velas) suben y el cierre está sobre la EMA20     |
//|    de ese marco. Ventas: al revés.                                |
//|  - Entrada (vela M5 cerrada): cierre sobre la EMA20 de M5, la     |
//|    vela tocó la EMA20 (+0,1 ATR) o el último mínimo de M5         |
//|    (+0,25 ATR) y cerró en su 40 % alto.                           |
//|  - SL: último mínimo de H1 - 0,1 ATR(M5) - 0,5 ATR(H1).           |
//|  - TP: 2 veces la distancia del SL. Cierre forzado a las 24 h.    |
//|  - Lote: el que arriesga RiesgoUSD en el SL.                      |
//|  - Máximo 2 operaciones abiertas por dirección.                   |
//| Ponerlo en un gráfico M5 de XAUUSDm. Probar primero en DEMO.      |
//+------------------------------------------------------------------+
#property copyright "BotScalping"
#property version   "1.00"
#property strict

#include <Trade/Trade.mqh>

input double RiesgoUSD      = 20.0;  // dólares arriesgados por operación
input int    MaxPorDireccion = 2;    // operaciones abiertas a la vez por dirección
input double RR             = 2.0;   // objetivo = RR x distancia del SL
input int    MaxHoras       = 24;    // cierre forzado
input double MargenATRH1    = 0.5;   // margen extra del SL bajo el mínimo de H1, en ATR(H1)
input int    K              = 3;     // velas a cada lado para confirmar un máximo/mínimo
input long   Magic          = 202611;

CTrade trade;
int hEmaM5, hEmaH1, hEmaH4, hAtrM5, hAtrH1;
datetime ultimaVela = 0;

double Buf(int h, int shift) { double b[1]; return CopyBuffer(h, 0, shift, 1, b) == 1 ? b[0] : 0; }

//--- últimos dos máximos y mínimos confirmados (fractal de K velas) en el marco tf, solo con velas cerradas
bool Swings(ENUM_TIMEFRAMES tf, double &sh1, double &sh2, double &sl1, double &sl2)
{
   int nH = 0, nL = 0; sh1 = sh2 = sl1 = sl2 = 0;
   for(int j = K + 1; j < 500 && (nH < 2 || nL < 2); j++)
   {
      double hj = iHigh(_Symbol, tf, j), lj = iLow(_Symbol, tf, j);
      if(hj == 0) return false;
      bool isH = true, isL = true;
      for(int m = j - K; m <= j + K; m++)
      {
         if(m == j) continue;
         if(iHigh(_Symbol, tf, m) > hj) isH = false;
         if(iLow(_Symbol, tf, m) < lj) isL = false;
      }
      if(isH && nH < 2) { if(nH == 0) sh1 = hj; else sh2 = hj; nH++; }
      if(isL && nL < 2) { if(nL == 0) sl1 = lj; else sl2 = lj; nL++; }
   }
   return nH == 2 && nL == 2;
}

int Tendencia(ENUM_TIMEFRAMES tf, int hEma, double &ultMin, double &ultMax)
{
   double sh1, sh2, sl1, sl2;
   if(!Swings(tf, sh1, sh2, sl1, sl2)) return 0;
   ultMin = sl1; ultMax = sh1;
   double c = iClose(_Symbol, tf, 1), e = Buf(hEma, 1);
   if(sh1 > sh2 && sl1 > sl2 && c > e) return 1;
   if(sh1 < sh2 && sl1 < sl2 && c < e) return -1;
   return 0;
}

int Abiertas(int dir)
{
   int n = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong tk = PositionGetTicket(i);
      if(!PositionSelectByTicket(tk) || PositionGetString(POSITION_SYMBOL) != _Symbol || PositionGetInteger(POSITION_MAGIC) != Magic) continue;
      long t = PositionGetInteger(POSITION_TYPE);
      if((dir == 1 && t == POSITION_TYPE_BUY) || (dir == -1 && t == POSITION_TYPE_SELL)) n++;
   }
   return n;
}

void CerrarViejas()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong tk = PositionGetTicket(i);
      if(!PositionSelectByTicket(tk) || PositionGetString(POSITION_SYMBOL) != _Symbol || PositionGetInteger(POSITION_MAGIC) != Magic) continue;
      if(TimeCurrent() - (datetime)PositionGetInteger(POSITION_TIME) >= MaxHoras * 3600) trade.PositionClose(tk);
   }
}

double Lote(double dist)
{
   double tv = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE), ts = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP), vmin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN), vmax = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   if(tv <= 0 || ts <= 0 || dist <= 0) return 0;
   double lot = MathFloor(RiesgoUSD / (dist / ts * tv) / step) * step;
   if(lot < vmin) { PrintFormat("SL de %.2f necesita lote %.3f < mínimo %.2f: se omite (arriesgaría más de %.0f $)", dist, lot, vmin, RiesgoUSD); return 0; }
   return MathMin(lot, vmax);
}

int OnInit()
{
   trade.SetExpertMagicNumber(Magic);
   hEmaM5 = iMA(_Symbol, PERIOD_M5, 20, 0, MODE_EMA, PRICE_CLOSE);
   hEmaH1 = iMA(_Symbol, PERIOD_H1, 20, 0, MODE_EMA, PRICE_CLOSE);
   hEmaH4 = iMA(_Symbol, PERIOD_H4, 20, 0, MODE_EMA, PRICE_CLOSE);
   hAtrM5 = iATR(_Symbol, PERIOD_M5, 14);
   hAtrH1 = iATR(_Symbol, PERIOD_H1, 14);
   if(hEmaM5 == INVALID_HANDLE || hEmaH1 == INVALID_HANDLE || hEmaH4 == INVALID_HANDLE || hAtrM5 == INVALID_HANDLE || hAtrH1 == INVALID_HANDLE)
      return INIT_FAILED;
   return INIT_SUCCEEDED;
}

void OnTick()
{
   CerrarViejas();
   datetime t0 = iTime(_Symbol, PERIOD_M5, 0);
   if(t0 == ultimaVela) return;            // una evaluación por vela M5 cerrada
   ultimaVela = t0;

   double minH1, maxH1, minH4, maxH4;
   int d1 = Tendencia(PERIOD_H1, hEmaH1, minH1, maxH1);
   int d4 = Tendencia(PERIOD_H4, hEmaH4, minH4, maxH4);
   if(d1 == 0 || d1 != d4) return;

   double o = iOpen(_Symbol, PERIOD_M5, 1), h = iHigh(_Symbol, PERIOD_M5, 1), l = iLow(_Symbol, PERIOD_M5, 1), c = iClose(_Symbol, PERIOD_M5, 1);
   double e = Buf(hEmaM5, 1), a = Buf(hAtrM5, 1), aH = Buf(hAtrH1, 1);
   if(e == 0 || a == 0 || aH == 0 || h <= l) return;
   double sh1, sh2, sl1, sl2;
   if(!Swings(PERIOD_M5, sh1, sh2, sl1, sl2)) return;
   double pos = (c - l) / (h - l);

   if(d1 == 1 && c > e && (l <= e + 0.1 * a || l <= sl1 + 0.25 * a) && pos >= 0.6 && Abiertas(1) < MaxPorDireccion)
   {
      double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double sl = minH1 - 0.1 * a - MargenATRH1 * aH;
      double dist = MathMax(ask - sl, 0.5 * a); sl = ask - dist;
      double lot = Lote(dist);
      if(lot > 0 && !trade.Buy(lot, _Symbol, ask, NormalizeDouble(sl, _Digits), NormalizeDouble(ask + RR * dist, _Digits), "Estructura"))
         Print("Error al comprar: ", trade.ResultRetcodeDescription());
   }
   if(d1 == -1 && c < e && (h >= e - 0.1 * a || h >= sh1 - 0.25 * a) && pos <= 0.4 && Abiertas(-1) < MaxPorDireccion)
   {
      double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double sl = maxH1 + 0.1 * a + MargenATRH1 * aH;
      double dist = MathMax(sl - bid, 0.5 * a); sl = bid + dist;
      double lot = Lote(dist);
      if(lot > 0 && !trade.Sell(lot, _Symbol, bid, NormalizeDouble(sl, _Digits), NormalizeDouble(bid - RR * dist, _Digits), "Estructura"))
         Print("Error al vender: ", trade.ResultRetcodeDescription());
   }
}
