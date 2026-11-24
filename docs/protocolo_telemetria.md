# Telemetria do medidor — proposta para SCRUM-14 e SCRUM-15

**Rascunho de integração; ainda não validado na placa.** O firmware de diagnóstico emite somente o estado de erro, acrescentando `adc_v_mv` e `adc_i_mv` com médias dos pinos em milivolts. Interface serial USB de bancada: 115200 baud, 8N1, UTF-8, um objeto JSON por linha (`\n`). A periodicidade definitiva será definida após medir a duração da aquisição. Este formato não define o enquadramento LoRa.

```json
{"t":123456,"estado":"OK","tipo":"AC","v":12.0,"i":0.5,"p":6.0}
```

| Campo | Tipo | Significado |
|---|---|---|
| `t` | inteiro | Milissegundos desde a inicialização; contador de 32 bits pode retornar a zero após aproximadamente 49,7 dias. |
| `estado` | string | `OK`, `SEM_CONTATO` ou `ERRO`. A detecção de contato ainda precisa de mecanismo validado. |
| `tipo` | string ou null | `AC`, `DC` ou `null` quando indeterminado. Não inferir DC apenas por ausência de cruzamentos. |
| `v` | número ou null | Volts: RMS para AC ou média com polaridade definida na calibração para DC. |
| `i` | número ou null | Ampères: RMS para AC ou média com sentido definido para DC. |
| `p` | número ou null | Watts de potência ativa, com convenção de sinal documentada na calibração. |

Usar `null` para grandezas indisponíveis, sem sensor ou inválidas; nunca substituir por zero. `OK` indica aquisição válida, não certifica precisão ou segurança. Quando houver saturação, falha de amostragem, calibração ausente ou outra falha detectada, informar `ERRO` e usar `null` nos valores afetados. `SEM_CONTATO` só pode ser emitido quando houver detecção efetiva de contato; tensão ou corrente zero isoladamente não comprovam desconexão. Com recepção truncada ou JSON inválido, o consumidor deve descartar a linha e aguardar a próxima; campos adicionais desconhecidos devem ser ignorados. Dados de depuração não devem ser emitidos no mesmo canal como linhas que pareçam telemetria.

Exemplo sem classificação nem valores confiáveis:

```json
{"t":123900,"estado":"ERRO","tipo":null,"v":null,"i":null,"p":null}
```

O aplicativo atual trabalha com dados simulados; este documento é um contrato proposto, não uma afirmação de compatibilidade já implementada.

## Extensão Wi-Fi (sonda, `firmware/sonda-wifi`)

Mesmo formato, transportado por TCP (porta 3333). O handshake usa `"baud": 9600`, que não se aplica ao Wi-Fi, e por isso não há SYNC. A telemetria acrescenta `"rele": "ABERTO"|"FECHADO"` (estado do K2). Comandos app → sonda, cada um respondido com um `ack`:

| Comando | Resposta | Efeito |
|---|---|---|
| `{"cmd":"RELE","estado":"FECHADO"}` | `{"ack":"RELE","estado":"FECHADO"}` | disjuntor do app → chave K2 (MOSFETs) |
| `{"cmd":"MODO","tipo":"DC"}` | `{"ack":"MODO","tipo":"DC"}` | modo do painel → canal de tensão lido (ZMPT ou divisor DC) |
| `{"cmd":"PING"}` | `{"ack":"PING"}` | keepalive a cada 2 s; após 6 s sem comandos a sonda abre a chave K2 |

Um comando inválido recebe `{"ack":"ERRO","motivo":"..."}`.

Sem ser pedido, a sonda manda `{"ack":"RELE","estado":"ABERTO","motivo":"SOBRECORRENTE","i":8.0}` quando abre a chave K2 por sobrecorrente (acima de 3 A, ou com o ADC do ACS712 fora da faixa). Essa mensagem também substitui a confirmação de um `RELE FECHADO` que disparou ao fechar. O app então abre o disjuntor e grava o evento.
