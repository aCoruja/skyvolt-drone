# Frame — peças atuais (Rev. 1.3)

3 peças impressas separadamente, todas dentro da mesa de impressão de 220×220mm:

| Peça | Arquivo | Qtd | Dimensões |
|---|---|---|---|
| Hub | `SkyVolt_Hub.stl` | 1 | 129,6×121,2mm |
| Braço | `SkyVolt_Arm.stl` | 6 | 154×26mm |
| Bandeja de eletrônica | `SkyVolt_Tray.stl` | 1 | 150×80mm |

Gerado pelo script paramétrico `skyvolt_frame.py` (FreeCAD, `freecad.cmd skyvolt_frame.py`). `SkyVolt_Assembly_Preview.*` é só visualização (hub + 6 braços + bandeja posicionados), não é peça de impressão.

Hub e braço se unem por encaixe lingueta/rasgo + 2 parafusos M3 por junta. Motor: RS1606 3300KV, pad com padrão de furação 12×12mm/4×M2 (assumido para a classe do motor — confirmar contra datasheet real antes de imprimir em lote, ver Seção 8 do documento). Braço já sai com base de fixação para servo SG90 (M2, 32,5mm de espaçamento). Bandeja carrega 2×ESP32-S3 (trilho dimensionado para o footprint oficial 70×28mm) e 2×módulo LoRa (baia genérica por abraçadeira, footprint do módulo ainda não confirmado).
