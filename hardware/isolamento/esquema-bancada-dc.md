# Esquema proposto de bancada DC — revisão 0

**Rascunho para revisão do professor, sem ensaio ou aprovação. Máximo planejado: 24 V DC de fonte isolada.** Não utilizar para rede, 100 V, polaridade invertida ou no drone. O circuito medido compartilha GND com o ESP32 e o USB, portanto não atende ao RNF02. Conferir o módulo real ACS712, a placa, fontes e instrumentos antes de montar.

```text
                       +----------------------------- R1 390k 1% ----+---- R3 1k ---- GPIO1
                       |                                              |      |
 Fonte isolada + ------+                                              R2    C1
                       |                                            10k     100nF
                       |                                              |      |
                       +---- IP+ [módulo ACS712-05B] IP- --- CARGA ---+------+---- Fonte -
                                                                              |
                                                                              +---- GND ESP32

 Módulo ACS712 VCC ---- 5 V estáveis da placa, conferir disponibilidade de corrente
 Módulo ACS712 GND ---- GND ESP32
 Módulo ACS712 OUT ---- R4 10k 1% ----+---- R6 1k ---- GPIO2
                                      |      |
                                    R5 10k  C2 100nF
                                      |      |
 GND ESP32 ---------------------------+------+
```

O ramo R1/R2 e o ramo de corrente compartilham apenas os terminais da fonte; a carga não pertence ao divisor. R3/R6 limitam corrente; C1/C2 filtram após os resistores de entrada. Com R4=R5, uma saída nominal de até 5 V do ACS712 resulta em até 2,5 V no ADC; com corrente zero, cerca de 1,25 V. Verificar a faixa de alimentação real do módulo, erros dos resistores, comportamento de desligamento e correntes em diodos de proteção do ESP32: os resistores e capacitores **não garantem proteção contra todas as falhas**. O ADC não deve receber sinal fora dos limites do datasheet em qualquer estado. Analisar e adicionar proteção adequada antes da montagem, inclusive desconexão de terra, reversão da fonte e energização de uma parte sem a outra.

R1/R2 fornecem nominalmente 0,6 V em 24 V; selecionar resistores de potência e tensão adequadas, conectores, fios e carga em função do limite de corrente. O circuito de referência usa polaridade positiva. Carga deve ser dimensionada para a tensão e potência dissipadas, e sensor não deve exceder os limites da variante real. Medir offset de corrente com circuito aberto e conferir a faixa da fonte. Verificar que fonte da carga é isolada da rede, do computador e de outros instrumentos antes de ligar qualquer cabo.

Saída do módulo ZMPT e circuito de AC permanecem indefinidos: modelos genéricos podem ter alimentação, saída e isolamento diferentes. Não ligar esse módulo ao ESP32 sem verificar seu esquema e adaptar nível; não ligar rede na protoboard. Para placa final com 220 V e isolamento, projetar a proteção de entrada e a barreira completa separadamente.
