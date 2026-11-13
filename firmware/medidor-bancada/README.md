# Firmware do medidor de bancada

**Diagnóstico de bancada, não um medidor operacional.** O programa lê GPIO1 e GPIO2, calcula médias em milivolts e emite uma linha JSON aproximadamente por segundo com `ERRO` e grandezas físicas nulas. Ele não classifica sinais nem calcula grandezas físicas; valores ADC são apenas para diagnóstico e calibração. Usar somente após revisão do esquema de baixa tensão. Contrato: [protocolo de telemetria](../../docs/protocolo_telemetria.md).

`medicao.h` implementa cálculo independente de hardware sobre pares de amostras físicas já calibradas: médias, RMS total, componente AC da tensão, potência ativa média e potência aparente. Para uma fonte DC constante, potência é V × I. Para AC, potência depende de pares sincronizados e do tratamento de offset e fase. A função experimental de classificação usa limiares, histerese e cruzamentos; retorna indeterminado em casos ambíguos. Ela só serve a um canal capaz de representar DC e ambos os semiciclos, com amostras uniformes e sem saturação. Limiares, frequência e janela precisam de validação real, e não se deve interpretar o resultado como proteção elétrica. O `.ino` ainda não chama essa função e não possui aquisição temporizada, detecção de saturação, aplicação ou armazenamento de coeficientes. O cálculo de RMS total preserva componente DC; o RMS AC subtrai a média da janela.

Após definir placa, esquema, sensores e limites, implementar aquisição ADC1 e calibração rastreável, controle de tempo entre canais e classificação com estado indeterminado; validar limitações e falhas antes de emitir `OK`. Nunca usar a classificação como proteção elétrica. O arquivo `.ino` destina-se ao Arduino-ESP32 para ESP32-S3, mas a versão da plataforma ainda não foi fixada nem compilada para a placa.

Para planejamento foram escolhidos GPIO1 e GPIO2 de uma ESP32-S3-DevKitC-1 e um ACS712 de 5 A; são referências provisórias descritas em [componentes de referência](../../hardware/isolamento/componentes-referencia.md), não uma configuração validada para aquisição.

Teste local da matemática, sem dispositivo:

```sh
g++ -std=c++11 -Wall -Wextra -pedantic tests/test_medicao.cpp -o /tmp/skyvolt-test-medicao
/tmp/skyvolt-test-medicao
```

Executar da raiz do repositório. O teste não comprova precisão de sensores, firmware na placa ou segurança elétrica.

`python3 firmware/medidor-bancada/calibrar.py arquivo.csv` ajusta uma reta a dados com cabeçalho `adc_mv,referencia`, um arquivo por canal. Coletar pontos reais com instrumento, guardar a unidade e validar em pontos independentes. O erro nos dados usados no ajuste não comprova precisão final.
