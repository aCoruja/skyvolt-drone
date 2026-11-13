# Componentes genéricos para começar o projeto de bancada

Seleção **provisória** para desenhar e planejar, não inventário confirmado. A disponibilidade, fabricante, versão do módulo e pinagem física devem ser conferidos antes da montagem. Nenhum destes itens, isoladamente, comprova o RNF02 ou permite ensaiar rede na protoboard.

| Função | Referência adotada | Observações |
|---|---|---|
| Controlador | ESP32-S3-DevKitC-1 | GPIO1/ADC1_CH0 para tensão e GPIO2/ADC1_CH1 para corrente, se disponíveis na placa real. |
| Corrente | Módulo ACS712 variante 5 A (ACS712ELCTR-05B) | Alimentação nominal 5 V; sensibilidade típica 185 mV/A antes de adaptar a saída. Verificar marcações e datasheet. |
| Tensão DC | Divisor 390 kΩ + 10 kΩ, valores nominais | Relação 40:1: 24 V produzem cerca de 0,6 V nominal; resolução e erro em baixa tensão precisam ser avaliados. Não isola e não define proteção. |
| Tensão AC | Módulo ZMPT101B genérico | Marca, alimentação, ganho, saída, isolamento e esquema reais a confirmar; não ligar à rede. |
| ADC | ADC1 integrado ao ESP32-S3 | Começar por ele; ADS1115 opcional apenas após avaliar taxa, erro e atraso entre canais. |
| Alimentação do ensaio | Fonte de bancada DC isolada, limitada em corrente, até 24 V | A fonte medida compartilha referência com o ESP32 no ensaio DC. Conferir isolamento em relação ao USB e a todos os instrumentos. |
| Referência | Multímetro digital; True RMS para AC quando disponível | Modelo, incerteza e faixa de frequência devem ser registrados. |
| Alimentação isolada e comunicação para RNF02 | Não selecionadas | Avaliar modelos exatos, tensão de trabalho, isolamento e datasheets; o protótipo com GND compartilhado não cumpre o RNF02. |

## Ligações planejadas para revisão — DC até 24 V

```text
                      tensão (medida em paralelo)
 Fonte isolada + ---- R1 390k ----+---- GPIO1 / ADC1_CH0
                                  |
                                R2 10k
                                  |
 Fonte isolada - -----------------+---- GND ESP32 / GND ACS712

                      corrente (medida em série)
 Fonte isolada + ---- entrada de corrente ACS712 ---- saída ---- carga ---- Fonte -

 5 V adequado ---- VCC ACS712
 GND ESP32 ------- GND ACS712
 OUT ACS712 ------ adaptação de nível e proteção A DEFINIR ------ GPIO2 / ADC1_CH1
```

Esboço de conexões, **não esquemático completo nem instrução de montagem**: faltam proteção contra falhas e transientes, seleção de resistores e seus limites, alimentação, adaptação de nível, desacoplamento e checagem de tensões nos pinos. A saída do ACS712 pode exceder os limites do ESP32 e não deve ser conectada diretamente. O exemplo de divisor é unipolar; polaridade invertida pode danificar o ADC. Obter revisão do professor e desenhar os componentes pendentes antes de energizar. Usar carga e limite de corrente adequados ao sensor; manter USB e qualquer instrumento externo dentro da análise dos caminhos de terra.

O ADC deve ser calibrado junto ao divisor e sensor reais, inclusive offset da corrente sem carga e ganho medidos; não tratar valores típicos como coeficientes de calibração. Em 24 V, a tensão no ADC com relação 40:1 é pequena, logo a meta de 2% não está garantida. O módulo ZMPT exige circuito e calibração próprios; não há como estabelecer conexões ou classificação de segurança confiáveis a partir apenas do nome genérico.

Referências: [Espressif — pinos ADC do ESP32-S3](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/schematic-checklist.html); [Allegro — datasheet ACS712](https://www.allegromicro.com/-/media/files/datasheets/acs712-datasheet.ashx); [TI — datasheet ADS1115](https://www.ti.com/lit/ds/symlink/ads1115.pdf).
