# Firmware do medidor de bancada

**Diagnóstico de bancada, não um medidor operacional.** O programa lê GPIO1 e GPIO2, calcula médias em milivolts e emite uma linha JSON aproximadamente por segundo com `ERRO` e grandezas físicas nulas. Ele não classifica sinais nem calcula grandezas físicas; valores ADC são apenas para diagnóstico e calibração. Usar somente após revisão do esquema de baixa tensão. Contrato: [protocolo de telemetria](../../docs/protocolo_telemetria.md).

`medicao.h` calcula médias, RMS, potência ativa e aparente e implementa classificação experimental. `processamento.h` aplica coeficientes e verifica limites de ADC antes desses cálculos; `medidor-bancada.ino` coleta 400 pares com período nominal de 500 µs e chama esse processamento. As leituras dos canais são sequenciais: o atraso entre canais pode distorcer a potência AC. A rotina detecta atrasos grosseiros na janela, mas isso não valida temporização, fase ou frequência real. A saída permanece `ERRO` por padrão, pois os marcadores de validação e os coeficientes em `configuracao.h` são apenas exemplos. A classificação só serve a um canal capaz de representar DC e ambos os semiciclos, com amostras uniformes e sem saturação. Limiares, frequência e janela exigem validação real; jamais usar a classificação como proteção elétrica.

Após definir placa, esquema, sensores e limites, calibrar ambos os canais e validar aquisição, saturação, temporização e defasagem antes de habilitar a configuração. O divisor DC proposto não é bipolar e não suporta a classificação automática AC/DC. O arquivo `.ino` destina-se ao Arduino-ESP32 para ESP32-S3, mas a versão da plataforma ainda não foi fixada nem compilada para a placa.

Para planejamento foram escolhidos GPIO1 e GPIO2 de uma ESP32-S3-DevKitC-1 e um ACS712 de 5 A; são referências provisórias descritas em [componentes de referência](../../hardware/isolamento/componentes-referencia.md), não uma configuração validada para aquisição.

Teste local da matemática, sem dispositivo:

```sh
g++ -std=c++11 -Wall -Wextra -pedantic tests/test_medicao.cpp -o /tmp/skyvolt-test-medicao
/tmp/skyvolt-test-medicao
g++ -std=c++11 -Wall -Wextra -pedantic tests/test_processamento.cpp -o /tmp/skyvolt-test-processamento
/tmp/skyvolt-test-processamento
g++ -std=c++11 -Wall -Wextra -pedantic -I tests/stubs -x c++ -c firmware/medidor-bancada/medidor-bancada.ino -o /tmp/skyvolt-ino.o
```

Executar da raiz do repositório. O teste não comprova precisão de sensores, firmware na placa ou segurança elétrica.

`python3 firmware/medidor-bancada/calibrar.py arquivo.csv` ajusta uma reta a dados com cabeçalho `adc_mv,referencia`, um arquivo por canal. Coletar pontos reais com instrumento, guardar a unidade e validar em pontos independentes. O erro nos dados usados no ajuste não comprova precisão final.
