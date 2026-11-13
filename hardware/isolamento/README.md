# RNF02 — isolamento da medição

**Estado: proposta conceitual para bancada até 24 V DC; não construída nem validada.** A arquitetura não autoriza conexão à rede ou a 100 V DC. O circuito final, os componentes e a proteção devem ser dimensionados e revisados com o professor antes de qualquer ensaio de tensão perigosa.

## Decisão provisória

Adotar a **opção 2: aquisição no domínio medido e transmissão digital isolada**, sujeita ao inventário e aos resultados de bancada. Ela permite estudar um mesmo caminho de aquisição para tensão AC e DC, com alimentação isolada e sem ligação condutiva intencional entre os domínios. Não demonstra por si só que o circuito suporta 220 V AC ou que é seguro sob falhas.

| Critério | Sensores com isolamento próprio | Aquisição no lado medido | Híbrida |
|---|---|---|---|
| Tensão AC e DC | Transformador de tensão mede AC, não DC; DC precisa de outra solução | Possível com condicionamento adequado para ambas | Caminhos separados |
| Corrente AC e DC | Depende do sensor: transformador de corrente é AC; Hall pode medir ambas | Possível com sensor e condicionamento adequados | Depende dos canais escolhidos |
| Integração | Simples para AC; módulos variam | ADC, alimentação e comunicação isoladas | Maior número de caminhos |
| Precisão e ruído | Dependem de sensores e montagem | Dados digitais evitam erro analógico de CTR, mas aquisição e comunicação ainda podem falhar | Dependem dos dois caminhos |

220 V AC **RMS senoidal** correspondem a aproximadamente 311 V de pico nominal. Tolerâncias, surtos e falhas exigem margem adicional, ainda não calculada. O requisito RNF02 também exige tolerar 220 V em caso de classificação incorreta; o front-end de contato precisa ser projetado para isso, independentemente do modo selecionado. A precisão e a faixa de frequência ainda dependem do SCRUM-14. Digitalizar não elimina erro do divisor, ADC, amostragem ou ruído.

## Esquemático conceitual e esboço de layout

Este diagrama representa conexões funcionais, não um esquemático elétrico completo ou placa pronta para fabricar. `GND_HV` é referência do circuito medido e pode estar em potencial perigoso; não é terra de proteção.

```text
 DOMÍNIO MEDIDO (GND_HV)        BARREIRA              DOMÍNIO DRONE (GND_LV)

 Entrada + / -
      │
      ▼
 [proteção + condicionamento]  <-- dimensionamento pendente
      │
      ▼
 [ADC ADS1115] -- I²C --> [MCU_HV] -- TX --> [isolador de dados] --> RX ESP32
                          alimentação HV       ║                   3,3 V LV
                                              ║
 [regulação HV, se necessária] <-- saída -- [DC-DC isolado] <-- 5 V LV
           │                                  ║                     │
        GND_HV                                ║                  GND_LV
                                              ║
                              nenhum outro caminho cruza a barreira
```

O ADC possui interface I²C: a UART indicada requer um microcontrolador no domínio medido. Alternativamente, pode-se usar um isolador I²C bidirecional apropriado, dispensando esse microcontrolador; as duas opções exigem alimentação e níveis lógicos compatíveis em cada lado. UART inversa para configuração exige um canal isolado adicional; o diagrama mostra apenas transmissão HV → LV. Não conectar programador USB, osciloscópio aterrado ou qualquer outro cabo entre domínios: alimentação, programação e instrumentos devem preservar a separação. Avaliar também todos os caminhos externos, conectores e carcaça.

O ADS1115 não aceita tensão negativa em seus pinos em relação ao seu GND durante operação normal. Para AC é necessário um deslocamento de nível e condicionamento/proteção que mantenham **cada pino** entre GND e VDD, inclusive em falhas e na energização; entrada diferencial não elimina esse limite. Medir RMS exige amostrar a forma de onda, considerar frequência, taxa efetiva de amostragem, filtragem e calibração. O ADS1115 é multiplexado e tem taxa total máxima de 860 amostras/s; verificar se atende às metas do SCRUM-14 para os canais e frequências desejados. A entrada DC também precisa contemplar polaridade e sobrecarga. Um shunt mede corrente **em série**, não deve ser colocado diretamente entre os terminais de tensão; faixa, potência, queda de tensão e método de inserção ainda não foram definidos. Um sensor Hall pode ser alternativa.

No desenho físico, posicionar entradas e condicionamento de um lado e ESP32/USB/bateria do outro, com uma faixa de separação contínua em todas as camadas. Somente componentes de barreira selecionados atravessam a faixa por seus terminais apropriados. Sem cobre, vias ou planos atravessando/sobrepondo domínios, inclusive camadas internas; manter terminais e conectores separados. Considerar rasgo sob a barreira apenas onde o fabricante e as regras de fabricação permitirem: dimensões, creepage e clearance serão determinados pelo projeto e pelo encapsulamento. **5 mm, 3 mm e rasgo de 1,5–2 mm não são valores universais nem comprovam conformidade com IEC 61010-1.** Considerar norma aplicável, isolamento básico/reforçado, tensão de trabalho, sobretensão/categoria de medição, grau de poluição, material, altitude, montagem e falhas; revisar com o professor.

## Componentes e inventário

O inventário do laboratório não consta no repositório. Registrar modelo completo, fabricante, quantidade e datasheet antes de escolher:

| Item | Disponibilidade/modelo | Verificações pendentes |
|---|---|---|
| Fonte de bancada ≤ 24 V DC e multímetro | A confirmar | Limite de corrente, resolução e calibração |
| ADS1115 e MCU para o lado medido | A confirmar | Tensões, frequência, canais, programação isolada |
| DC-DC isolado | A confirmar | Tensão de trabalho contínua, classe de isolamento, transientes, certificação, distâncias, carga mínima e regulação |
| Isolador digital ou optoacoplador | A confirmar | Encapsulamento, classe de isolamento, tensão de trabalho, níveis, velocidade e direção |
| Resistores, proteção e sensor de corrente | A confirmar | Tensão por componente, potência, tolerância, falhas e faixa de corrente |

Uma classificação de ensaio como 1,5 kV DC não estabelece, sozinha, tensão de trabalho contínua nem isolamento adequado de segurança. B0505S-1W, PC817, 6N137, H11L1 e ISO7721 são apenas candidatos, não componentes aprovados: identificar fabricante, versão e encapsulamento e verificar datasheets. Uma saída nominal de 5 V do conversor não garante 5 V regulados; verificar carga e compatibilidade com ADC e MCU. Uma UART com PC817 em 9600 baud é somente hipótese de ensaio; corrente do LED, resistores, carga e tempos de chaveamento determinam se funciona.

## Plano de bancada — somente até 24 V DC

Não realizar teste de rede neste card. Antes da montagem, confirmar com o professor o circuito de baixa tensão, os limites dos instrumentos e que nenhuma conexão externa cria terra comum. A fonte de entrada precisa ser isolada do domínio LV e dos demais instrumentos. Usar limite de corrente adequado. O protótipo de bancada pode usar condicionamento específico de baixa tensão e não comprova o front-end de rede.

1. Com tudo desligado e desconectado, inspecionar visualmente e medir resistência entre vários pontos acessíveis do domínio medido, inclusive GND_HV, e GND_LV, com as polaridades do multímetro invertidas. Registrar instrumento, escala e leitura; esperar OL/fora de escala. Verificar também outros caminhos possíveis. Esse teste encontra curtos grosseiros, mas **não certifica** isolamento, fuga sob tensão, distância ou segurança em rede.
2. Alimentar somente o lado LV com 5 V e verificar a saída do DC-DC **entre seus próprios terminais secundários**, sob carga prevista e dentro dos limites do datasheet. Não interpretar uma tensão flutuante entre domínios como prova de isolamento: capacitância e impedância do multímetro podem produzir leituras variáveis.
3. Exercitar o enlace digital com valores conhecidos, contador de sequência e checksum/CRC; registrar quantidade de pacotes, perdas e erros. Com PC817, experimentar 9600 baud inicialmente e somente aumentar se necessário e demonstrado sem erros durante um ensaio documentado. Uma quantidade finita sem erro não prova ausência absoluta de erros.
4. Aplicar pontos DC entre 0 e 24 V à entrada de baixa tensão, sem ultrapassar os limites do circuito, e comparar a grandeza recebida no ESP32 com um multímetro de referência ligado somente ao domínio medido. Registrar referência, leitura, erro absoluto e, para referência diferente de zero, erro percentual `100 × |leitura − referência| / |referência|`. Em zero registrar erro absoluto; avaliar pontos crescentes e decrescentes e repetir leituras. Separar calibração de verificação.
5. Comparar resultados com as metas sugeridas no SCRUM-14: erro de até 2% em tensão DC e até 5% em tensão AC e corrente, sujeitas a ajuste com equipe e professor. A medição de ponta a ponta inclui sensor e ADC; para avaliar especificamente o enlace, comparar valores digitais antes e depois da barreira usando meios que não a ponteiem. Ensaios DC não validam RMS AC, corrente ou desempenho em alta tensão.

### Registro para preencher durante o ensaio

- Data, responsáveis, esquema/revisão e foto: **pendentes**.
- Instrumentos, modelos, calibração, fonte, limite de corrente e componentes exatos: **pendentes**.
- Resistência, pontos testados, escala e polaridades: **pendentes**.
- Tensão secundária e carga: **pendentes**.
- Protocolo, baud, duração, pacotes enviados/recebidos, perdas e erros: **pendentes**.
- Tabela de referência, leitura, erro e critério do SCRUM-14: **pendentes**.
- Resultado, anomalias e assinatura do responsável: **pendentes**.

## Aceitação e próximos passos

- [x] Opção 2 escolhida provisoriamente e justificada.
- [ ] Inventário levantado; decisão confirmada com o laboratório.
- [ ] Esquemático elétrico completo, revisado e commitado; o diagrama acima é conceitual.
- [ ] Protótipo até 24 V DC montado e teste de resistência registrado.
- [ ] Metas sugeridas do SCRUM-14 confirmadas com a equipe e precisão demonstrada na faixa testada.
- [x] Esboço conceitual de separação e requisitos de layout documentados; dimensões finais pendentes.
- [ ] Front-end, barreira, proteção, normas e plano de validação para tensão perigosa revisados pelo professor antes de prosseguir.

## Referências

- [Documento técnico do projeto, RNF02 e RNF06](../../docs/SkyVolt_Documento.tex).
- [TI — datasheet ADS1115: limites de entrada, multiplexação e taxa](https://www.ti.com/lit/ds/symlink/ads1115.pdf).
- [TI — seleção de isolamento, tensão de trabalho, creepage e clearance](https://www.ti.com/document-viewer/lit/html/SSZTBV8): exemplo de aplicação de norma para acionamentos; não substitui a norma aplicável ao SkyVolt.
- [RECOM — exemplo de DC-DC com tensão de ensaio e duração especificadas](https://recom-power.com/en/rec-p-RB-0505S%21sHP.html).
