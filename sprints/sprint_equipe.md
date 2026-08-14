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

### Prioridade 1 — kit de prática
- [ ] Kit DIY toothpick/tiny whoop (3"–4"): frame + 4 motores brushless pequenos + ESC 4-em-1 + FC + hélices — **~R$150–300**

### Prioridade 2 — ferramentas (pular o que já tem)
- [ ] Soldador de ponta fina + solda + fluxo
- [ ] Alicate de corte (flush cutter)
- [ ] Kit de chave allen/hex (M2/M2,5/M3) — já serve pro SkyVolt depois
- [ ] Multímetro
- [ ] Termorretrátil (várias espessuras)
- [ ] Álcool isopropílico

### Prioridade 3 — energia e segurança
- [ ] Bateria pequena (1S/2S, geralmente já vem no kit) + carregador USB balanceado
- [ ] **LiPo bag** (bolsa retardante) — obrigatório, não opcional

### Prioridade 4 — treino sem gastar peça
- [ ] Simulador de voo (Liftoff, Velocidrone ou FPV Freerider gratuito)

### Bônus — valida uma pendência real do SkyVolt
- [ ] 1× motor RS1606 3300KV avulso + parafusos M2 (~R$35–70) — testar contra `SkyVolt_Arm.stl` antes de comprar os 6 motores de verdade

**Total estimado da trilha:** ~R$300–500.

## Observação

Isso é aprendizado da equipe, não é código auditado por commit — mas registrar o processo (fotos, o que funcionou/não funcionou) é material bom pra `notebooks/` ou pra enriquecer a Seção 8 (Pendências) do documento quando a fase 4 confirmar ou corrigir o padrão de furação do motor.
