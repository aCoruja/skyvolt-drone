# Sprint Equipe — trilha prática de hardware (paralela, não bloqueia entregas)

Diferente das sprints do `roadmap.md` (que seguem o calendário do professor e valem nota), esta é uma trilha da própria equipe: aprender montagem física de drone na prática, em paralelo, sem pressa e sem travar a A1/1 nem as entregas seguintes. Hardware só é exigido de verdade a partir da Sprint 11 do roadmap (Unidade 4, 20/10/2026) — essa trilha existe pra equipe chegar lá já com prática de solda, montagem e voo, em vez de aprender tudo em cima da hora.

## Linha do tempo

| Fase | Período | O que fazer |
|---|---|---|
| **1 — Compra** | 14/08 – 24/08 | Comprar o kit de prática e ferramentas (lista abaixo) — pedir logo, mesmo com a equipe focada na A1/1, pra já chegar durante a fase 2 |
| **2 — Montagem** | 25/08 – 14/09 | Montar o kit DIY: soldar motor no ESC, flashar firmware (Betaflight), parafusar frame, balancear hélice. Em paralelo às sprints 2–5 do roadmap, no tempo livre da equipe |
| **3 — Simulador + voo** | 15/09 – 05/10 | Treinar no simulador (Liftoff/Velocidrone/FPV Freerider) antes de qualquer voo real; primeiro voo real do kit de prática se a equipe se sentir segura |
| **4 — Validação SkyVolt** | 06/10 – 19/10 | Testar o motor RS1606 avulso encaixando no pad impresso do braço (`hardware/frame/SkyVolt_Arm.stl`) — confirma ou derruba a suposição de furação 12×12mm do CAD antes da Unidade 4 começar |

Fase 4 termina bem antes da Sprint 11 do roadmap (Unidade 4, 20/10) — dá folga real, não é em cima da hora.

## Lista de compras

Links do AliExpress (mais barato, prazo 2-6 semanas — cabe no cronograma da Fase 1). Critério de confiança: selo **"Choice"**, loja ≥4.7, milhares de "orders", ler as reviews com foto mais recentes.

### Prioridade 1 — kit de prática
- [ ] Motor pequeno (classe 1103-1404) — [BetaFPV 1404 3800KV](https://www.aliexpress.com/item/4001209475809.html)
- [ ] ESC + FC (procurar combo "AIO" pra esse frame, ainda não achei um específico confiável — conferir direto na busca [fpv drone parts](https://www.aliexpress.com/w/wholesale-fpv-drone-parts.html))
- Total estimado: **~R$150–300**

### Prioridade 2 — ferramentas (pular o que já tem)
- [ ] Soldador de ponta fina — [busca: kit ferro de solda](https://www.aliexpress.com/w/wholesale-soldering-iron-kit.html) (escolher um com regulagem de temperatura)
- [ ] Alicate de corte (flush cutter) — [Libraton Micro Wire Cutter 5.12"](https://www.aliexpress.com/item/1005006301271062.html)
- [ ] Kit de chave allen/hex — [7pçs 0,7-3mm](https://www.aliexpress.com/item/32904829892.html) — já serve pro SkyVolt depois (M2/M3)
- [ ] Multímetro — [HoldPeak HP-36K mini](https://www.aliexpress.com/item/HoldPeak-HP-36K-DC-AC-Mini-Digital-Multimeter-3999-Display-Portable-Resistance-Capacitor-Frequency-Meter-Measuring/32831008802.html)
- [ ] Termorretrátil — [kit 164pçs, 8 tamanhos](https://www.aliexpress.com/item/32985677716.html)
- [ ] Álcool isopropílico — **comprar local** (farmácia/loja de eletrônica), não compensa pedir importado

### Prioridade 3 — energia e segurança
- [ ] Bateria 1S/2S pequena — geralmente já vem no kit da Prioridade 1; se não vier, [busca: bateria lipo 1S](https://www.aliexpress.com/w/wholesale-1s-lipo-battery.html)
- [ ] Carregador USB balanceado — [EMAX charger 1S/2S USB](https://www.aliexpress.com/item/33063462223.html)
- [ ] **LiPo bag** (bolsa retardante, obrigatório) — [Ovonic 260×130×180mm](https://www.aliexpress.com/item/1005001727772122.html) ou [HRB à prova de fogo](https://www.aliexpress.com/item/1005004144090727.html)

### Prioridade 4 — treino sem gastar peça
- [ ] Simulador de voo (Liftoff/Velocidrone — pagos, Steam; FPV Freerider — gratuito) — não é AliExpress, é software

### Bônus — valida uma pendência real do SkyVolt
- [ ] 1× motor RS1606 3300KV avulso — [EMAX RS1606 3300KV/4000KV, US$22,15](https://www.aliexpress.com/item/4001075493603.html) (loja oficial EMAX se aparecer, vale pagar mais por procedência aqui — esse item valida uma medida crítica do CAD) + parafusos M2 — testar contra `SkyVolt_Arm.stl` antes de comprar os 6 motores de verdade

**Total estimado da trilha:** ~R$300–500 (câmbio do dia).

## Observação

Isso é aprendizado da equipe, não é código auditado por commit — mas registrar o processo (fotos, o que funcionou/não funcionou) é material bom pra `notebooks/` ou pra enriquecer a Seção 8 (Pendências) do documento quando a fase 4 confirmar ou corrigir o padrão de furação do motor.
