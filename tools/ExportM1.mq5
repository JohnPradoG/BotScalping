// Exporta barras M1 (bid) con tick volume y spread a MQL5/Files, formato del exportador de MT5.
// Solo lectura: no envia ordenes.
string Symbols[] = {"XAUUSDm", "USTECm"};

bool ExportSymbol(string sym)
  {
   SymbolSelect(sym, true);
   string fname = "ExportM1_" + sym + ".csv";
   int h = FileOpen(fname, FILE_WRITE|FILE_TXT|FILE_ANSI);
   if(h == INVALID_HANDLE) { Print("No se pudo abrir ", fname); return false; }
   FileWriteString(h, "<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\t<VOL>\t<SPREAD>\r\n");
   int digits = (int)SymbolInfoInteger(sym, SYMBOL_DIGITS);
   datetime first = 0;
   for(int k = 0; k < 50 && first == 0; k++) { first = (datetime)SeriesInfoInteger(sym, PERIOD_M1, SERIES_SERVER_FIRSTDATE); if(first == 0) Sleep(200); }
   if(first == 0) first = D'2010.01.01';
   Print(sym, " primera fecha en servidor: ", TimeToString(first));
   long total = 0;
   datetime now = TimeCurrent();
   for(datetime from = first; from <= now; from += 30*86400)
     {
      datetime to = from + 30*86400 - 1;
      MqlRates r[];
      int n = -1;
      for(int t = 0; t < 40; t++) { n = CopyRates(sym, PERIOD_M1, from, to, r); if(n >= 0) break; Sleep(250); }
      if(n <= 0) continue;
      for(int i = 0; i < n; i++)
        {
         MqlDateTime dt; TimeToStruct(r[i].time, dt);
         FileWriteString(h, StringFormat("%04d.%02d.%02d\t%02d:%02d:%02d\t%s\t%s\t%s\t%s\t%I64d\t%I64d\t%d\r\n",
                         dt.year, dt.mon, dt.day, dt.hour, dt.min, dt.sec,
                         DoubleToString(r[i].open, digits), DoubleToString(r[i].high, digits),
                         DoubleToString(r[i].low, digits), DoubleToString(r[i].close, digits),
                         r[i].tick_volume, r[i].real_volume, r[i].spread));
        }
      total += n;
     }
   FileClose(h);
   Print(sym, " exportado: ", total, " barras, point=", DoubleToString(SymbolInfoDouble(sym, SYMBOL_POINT), digits));
   return true;
  }

void OnStart()
  {
   for(int i = 0; i < ArraySize(Symbols); i++) ExportSymbol(Symbols[i]);
   Print("ExportM1 listo");
  }
