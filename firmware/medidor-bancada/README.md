# Firmware do medidor de bancada

**Esqueleto, não um medidor operacional.** O programa emite uma linha JSON por segundo com `ERRO` e grandezas nulas; não acessa sensores nem classifica sinais. Isso impede que pinos, componentes ou coeficientes desconhecidos gerem leituras aparentemente válidas. Contrato: [protocolo de telemetria](../../docs/protocolo_telemetria.md).

`medicao.h` implementa cálculo independente de hardware sobre pares de amostras físicas já calibradas: médias, RMS total, componente AC da tensão e potência ativa média. Para uma fonte DC constante, potência é V × I. Para AC, potência depende de pares sincronizados e do tratamento de offset e fase. Não existe ainda aquisição temporizada, detecção de saturação, classificação, calibração ou armazenamento de coeficientes. O cálculo de RMS total preserva componente DC; o RMS AC subtrai a média da janela.

Após definir placa, esquema, sensores e limites, implementar aquisição ADC1 e calibração rastreável, controle de tempo entre canais e classificação com estado indeterminado; validar limitações e falhas antes de emitir `OK`. Nunca usar a classificação como proteção elétrica. O arquivo `.ino` destina-se ao Arduino-ESP32 para ESP32-S3, mas a versão da plataforma ainda não foi fixada nem compilada para a placa.

Teste local da matemática, sem dispositivo:

```sh
g++ -std=c++11 -Wall -Wextra -pedantic tests/test_medicao.cpp -o /tmp/skyvolt-test-medicao
/tmp/skyvolt-test-medicao
```

Executar da raiz do repositório. O teste não comprova precisão de sensores, firmware na placa ou segurança elétrica.
