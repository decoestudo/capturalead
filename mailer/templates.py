"""
20 variações de email HTML para campanha TopAgenda.
Cada variante tem identidade visual e ângulo de copy próprios.
"""

SUBJECTS = [
    "Seu negócio ainda agenda pelo WhatsApp?",
    "Enquanto você atende, clientes estão tentando marcar horário",
    "3 motivos pelos quais você perde clientes sem perceber",
    "Acabou o horário que não apareceu — veja como evitar isso",
    "Seu concorrente já automatizou a agenda. E você?",
    "Agenda cheia todo dia — sem responder mensagem",
    "Chega de cliente faltando sem avisar",
    "Como negócios de serviço estão lotando a agenda no piloto automático",
    "Você ainda gerencia sua agenda manualmente?",
    "Automatize sua agenda e foque no que importa",
    "Clientes somem quando não conseguem marcar online — sabia?",
    "O segredo dos negócios com agenda sempre cheia",
    "Quanto você perdeu hoje por não ter agendamento online?",
    "3 minutos para transformar a gestão da sua agenda",
    "Seus clientes marcam com o concorrente porque é mais fácil",
    "Nunca mais perca um cliente por falta de disponibilidade",
    "A agenda que trabalha enquanto você descansa",
    "Teste grátis: para ver a diferença na sua agenda",
    "Reduza faltas e aumente o faturamento — veja como",
    "Seu negócio merece uma agenda profissional",
]

# 20 variantes de conteúdo: accent, bg1, bg2, headline, sub, pain (3 itens), solution, cta, testimonial
VARIANTS = [
    {   # 1 — vermelho: dor de perder clientes
        "accent": "#E53E3E", "bg1": "#1a0a0a", "bg2": "#2d0f0f",
        "headline": "Você ainda perde clientes por falta de agenda online?",
        "sub": "Enquanto você está atendendo, outros clientes estão ligando — e desistindo.",
        "pain": [
            "😩 São 23h e você ainda responde 'que horário tem disponível?' no WhatsApp",
            "😤 Dois clientes chegaram ao mesmo tempo porque os horários se confundiram",
            "💸 O cliente marcou, não apareceu e você ficou com o horário vazio sem receber nada",
        ],
        "solution": "Com o <strong style='color:#fff'>TopAgenda</strong>, seus clientes marcam online a qualquer hora — você só recebe a confirmação. Sem confusão, sem WhatsApp, sem estresse.",
        "cta": "🚀 Quero minha agenda online agora",
        "testimonial": "Antes eu perdia clientes toda semana. Depois do TopAgenda, minha agenda lotou e parei de ficar no celular o dia todo. Vale cada centavo.",
    },
    {   # 2 — verde: agenda cheia
        "accent": "#38A169", "bg1": "#0a1a0f", "bg2": "#0f2d18",
        "headline": "Agenda cheia todos os dias — sem depender de mensagem",
        "sub": "Automatize seus agendamentos e foque no que você faz de melhor.",
        "pain": [
            "📱 Você passa horas por dia respondendo mensagens de agendamento",
            "🗓️ Sua agenda tem horários vazios que poderiam estar preenchidos",
            "😓 Você depende 100% de estar disponível para marcar um horário",
        ],
        "solution": "O <strong style='color:#fff'>TopAgenda</strong> cuida da sua agenda enquanto você cuida dos seus clientes. Confirmações automáticas, lembretes e gestão tudo em um só lugar.",
        "cta": "✅ Começar agora — é grátis",
        "testimonial": "Em uma semana minha agenda já estava cheia. Não preciso mais ficar no celular confirmando horário por horário. Incrível!",
    },
    {   # 3 — azul: adeus WhatsApp
        "accent": "#3182CE", "bg1": "#0a0f1a", "bg2": "#0f1d2d",
        "headline": "Adeus ao caos de agendamentos no WhatsApp",
        "sub": "Seu tempo vale ouro. Pare de desperdiçar respondendo mensagem por mensagem.",
        "pain": [
            "📲 WhatsApp lotado de 'tem horário hoje?' enquanto você está atendendo",
            "🔔 Notificações o dia todo interrompendo seu trabalho e sua concentração",
            "😵 Fim de dia: cansado de atender e ainda precisando responder mensagens",
        ],
        "solution": "Com o <strong style='color:#fff'>TopAgenda</strong>, seus clientes marcam online em segundos. Você recebe a confirmação e foca 100% no atendimento — sem interrupções.",
        "cta": "💬 Acabar com o caos agora",
        "testimonial": "Meu WhatsApp finalmente ficou em paz. Os clientes agendam sozinhos e eu só apareço para atender. Mudou minha vida profissional.",
    },
    {   # 4 — roxo: confirmação automática
        "accent": "#805AD5", "bg1": "#0f0a1a", "bg2": "#1a0f2d",
        "headline": "Confirmação automática = cliente que realmente aparece",
        "sub": "Reduza as faltas e cancelamentos de última hora com lembretes inteligentes.",
        "pain": [
            "😤 Cliente que marca e não aparece — sem avisar, sem cancelar",
            "💰 Cada falta é dinheiro que você perdeu e não vai recuperar",
            "📞 Você precisa ligar para confirmar horário um por um manualmente",
        ],
        "solution": "O <strong style='color:#fff'>TopAgenda</strong> envia lembretes automáticos por WhatsApp e email. Seus clientes chegam na hora certa e você não perde faturamento por falta.",
        "cta": "🔔 Eliminar faltas agora",
        "testimonial": "As faltas caíram mais de 70% depois que comecei a usar o TopAgenda. Os lembretes automáticos fazem toda a diferença.",
    },
    {   # 5 — âmbar: estatística impactante
        "accent": "#D69E2E", "bg1": "#1a130a", "bg2": "#2d1f0f",
        "headline": "73% dos clientes desistem quando não podem marcar online",
        "sub": "Não deixe seu negócio fazer parte dessa estatística.",
        "pain": [
            "📊 Mais da metade dos clientes prefere marcar online a ligar ou mandar mensagem",
            "🏃 Se o processo for difícil, eles vão embora — e marcam com o concorrente",
            "⏰ Clientes querem marcar às 21h, no domingo, na hora que é conveniente pra eles",
        ],
        "solution": "O consumidor moderno quer praticidade. Com o <strong style='color:#fff'>TopAgenda</strong>, você oferece agendamento online 24h por dia, 7 dias por semana — e captura clientes que você perderia.",
        "cta": "📈 Ativar agendamento online",
        "testimonial": "Comecei a receber agendamentos de madrugada, de domingo, de horários que eu nunca imaginaria. O TopAgenda captura clientes que eu perderia.",
    },
    {   # 6 — verde-azulado: produtividade
        "accent": "#319795", "bg1": "#0a1a1a", "bg2": "#0f2d2d",
        "headline": "Agende mais, trabalhe menos",
        "sub": "A automação que transforma a rotina do seu negócio.",
        "pain": [
            "⏳ Você gasta mais de 2 horas por dia apenas gerenciando sua agenda",
            "📋 Papel, caderno, planilha — cada um tem suas limitações e erros",
            "🤯 Difícil saber o que está agendado, o que foi cancelado, o que está pendente",
        ],
        "solution": "Imagine acordar e já ter novos agendamentos confirmados. Com o <strong style='color:#fff'>TopAgenda</strong>, seu negócio trabalha mesmo quando você não está — agenda preenchida, clientes satisfeitos.",
        "cta": "⚡ Ver como funciona",
        "testimonial": "Economizo pelo menos 2 horas por dia que antes gastava gerenciando agenda. Agora uso esse tempo para atender mais clientes e ganhar mais.",
    },
    {   # 7 — azul escuro: trabalha enquanto dorme
        "accent": "#2B6CB0", "bg1": "#070d1a", "bg2": "#0c1829",
        "headline": "O sistema que trabalha por você enquanto você dorme",
        "sub": "Agendamento online, lembretes e gestão tudo em um só lugar.",
        "pain": [
            "🌙 Sua agenda 'fecha' quando você vai dormir — e perde clientes noturnos",
            "📵 Fins de semana e feriados: ninguém disponível para confirmar horários",
            "🔄 Cada agendamento manual exige sua atenção e seu tempo",
        ],
        "solution": "Enquanto você descansa, o <strong style='color:#fff'>TopAgenda</strong> está captando novos clientes e preenchendo sua agenda. Desperte com horários confirmados e clientes esperando.",
        "cta": "🌙 Quero isso para o meu negócio",
        "testimonial": "Na primeira semana, acordei com 5 agendamentos novos que entraram durante a noite. Nunca mais vou gerenciar agenda manualmente.",
    },
    {   # 8 — laranja: imagem profissional
        "accent": "#DD6B20", "bg1": "#1a0f05", "bg2": "#2d1a0a",
        "headline": "Seu negócio merece uma presença profissional",
        "sub": "Clientes avaliam sua imagem antes de marcar horário — e isso define se eles escolhem você.",
        "pain": [
            "👀 Clientes pesquisam você online antes de ligar — e julgam o que veem",
            "📱 Uma página de agendamento profissional transmite confiança e credibilidade",
            "🏆 Negócios com presença digital profissional faturam até 40% mais",
        ],
        "solution": "Com o <strong style='color:#fff'>TopAgenda</strong>, você tem uma página de agendamento bonita, rápida e profissional. Seus clientes ficam impressionados desde o primeiro contato.",
        "cta": "🎨 Profissionalizar meu negócio",
        "testimonial": "Clientes novos sempre comentam como é fácil e bonito o meu sistema de agendamento. Isso passou uma imagem muito mais profissional do meu salão.",
    },
    {   # 9 — dourado: nenhum horário vazio
        "accent": "#B7791F", "bg1": "#1a1205", "bg2": "#2d1f08",
        "headline": "Não perca mais nenhum horário vago na sua agenda",
        "sub": "Cada horário vazio é dinheiro que ficou na mesa.",
        "pain": [
            "💸 Horários vagos = faturamento perdido que não volta mais",
            "📉 Cancelamentos de última hora deixam buracos difíceis de preencher",
            "📞 Você não tem tempo de ligar para lista de espera quando alguém cancela",
        ],
        "solution": "O <strong style='color:#fff'>TopAgenda</strong> preenche automaticamente os buracos na sua agenda com clientes da lista de espera. Quando alguém cancela, outro entra — sem você fazer nada.",
        "cta": "💰 Preencher minha agenda",
        "testimonial": "Antes eu ficava com horários vazios toda semana. Agora quando alguém cancela, o sistema já chama o próximo da fila. Zero horário perdido.",
    },
    {   # 10 — verde escuro: crescimento
        "accent": "#276749", "bg1": "#071a0f", "bg2": "#0c2d1a",
        "headline": "Como dobrar sua clientela sem gastar mais em marketing",
        "sub": "A resposta está na facilidade de marcar horário com você.",
        "pain": [
            "📢 Você gasta em anúncio mas perde clientes na hora de marcar horário",
            "🔗 O processo de agendamento complicado afasta quem teria virado cliente",
            "💬 Indicações se perdem quando a pessoa não consegue marcar facilmente",
        ],
        "solution": "Clientes indicam negócios que oferecem boa experiência. Com o <strong style='color:#fff'>TopAgenda</strong>, marcar horário é tão fácil que seus clientes indicam espontaneamente — crescimento orgânico de verdade.",
        "cta": "📈 Quero mais clientes",
        "testimonial": "Minha clientela dobrou em 3 meses sem gastar um real a mais em propaganda. Só pelo fato de ter agendamento fácil, as indicações explodiram.",
    },
    {   # 11 — índigo: vantagem competitiva
        "accent": "#553C9A", "bg1": "#0d0a1a", "bg2": "#17122d",
        "headline": "A solução que seus concorrentes ainda não descobriram",
        "sub": "Saia na frente antes que eles acordem.",
        "pain": [
            "🏃 Seus concorrentes diretos estão adotando tecnologia — você está pronto?",
            "⚡ Quem automatizar primeiro vai capturar os clientes que os outros perderão",
            "📱 O mercado está mudando: clientes escolhem o que é mais fácil e moderno",
        ],
        "solution": "Enquanto outros ainda dependem de WhatsApp e cadernos, você pode automatizar tudo com o <strong style='color:#fff'>TopAgenda</strong> — e atender mais clientes com menos esforço. Seja o primeiro na sua região.",
        "cta": "🥇 Sair na frente agora",
        "testimonial": "Fui o primeiro do meu bairro a ter agendamento online. Em 60 dias já era o mais buscado da região. TopAgenda mudou meu negócio.",
    },
    {   # 12 — violeta: reduzir faltas
        "accent": "#6B46C1", "bg1": "#0f0a1a", "bg2": "#1a1030",
        "headline": "Reduza faltas em até 60% com lembretes automáticos",
        "sub": "Cliente que lembra do horário é cliente que aparece.",
        "pain": [
            "😤 Faltas constantes desequilibram seu dia e seu faturamento",
            "📞 Confirmar horário por ligação toma tempo e nem sempre funciona",
            "💔 Cada falta é uma vaga que poderia ter sido de um cliente pagante",
        ],
        "solution": "O <strong style='color:#fff'>TopAgenda</strong> envia lembretes automáticos 24h antes do agendamento — por WhatsApp e email. Sem faltas surpresa, sem horários perdidos, sem prejuízo no faturamento.",
        "cta": "🔕 Eliminar faltas agora",
        "testimonial": "Minhas faltas caíram de 8-10 por semana para menos de 2. O lembrete automático faz um trabalho que eu não conseguia fazer manualmente.",
    },
    {   # 13 — rosa: menos WhatsApp
        "accent": "#D53F8C", "bg1": "#1a0a12", "bg2": "#2d0f1f",
        "headline": "Menos tempo no WhatsApp, mais tempo para seus clientes",
        "sub": "Você não abriu seu negócio para responder mensagem o dia todo.",
        "pain": [
            "📲 Dezenas de mensagens por dia só para marcar e confirmar horários",
            "😤 Interrupções constantes enquanto você tenta trabalhar e atender",
            "🌙 Noites respondendo mensagens que poderiam ter sido evitadas",
        ],
        "solution": "Com o <strong style='color:#fff'>TopAgenda</strong>, os agendamentos acontecem sozinhos. Você foca no que realmente importa: atender bem, fidelizar clientes e fazer seu negócio crescer.",
        "cta": "✂️ Libertar meu tempo agora",
        "testimonial": "Passava 3 horas por dia no WhatsApp só com agendamentos. Hoje esse tempo zero — e uso para dar um atendimento melhor para quem está comigo.",
    },
    {   # 14 — escuro: agendamentos 24h
        "accent": "#4299E1", "bg1": "#05080f", "bg2": "#081020",
        "headline": "Agendamentos entrando às 2h da manhã enquanto você dorme",
        "sub": "Seu negócio não para — mesmo quando você para.",
        "pain": [
            "🌙 Clientes tentam marcar fora do horário comercial e desistem",
            "📅 Fins de semana e feriados: sua agenda fica estagnada",
            "⏰ Você só pode receber agendamentos quando está disponível para responder",
        ],
        "solution": "Com o <strong style='color:#fff'>TopAgenda</strong>, clientes marcam horário online a qualquer hora. De madrugada, fim de semana, feriado — sua agenda nunca fecha e nunca para de crescer.",
        "cta": "🌙 Abrir minha agenda 24h",
        "testimonial": "Acordei na segunda-feira com 12 agendamentos novos que entraram no final de semana. Sem o TopAgenda eu teria perdido todos esses clientes.",
    },
    {   # 15 — cinza ardósia: experiência do cliente
        "accent": "#718096", "bg1": "#0f1114", "bg2": "#1a1d24",
        "headline": "Seu negócio na palma da mão dos seus clientes",
        "sub": "O agendamento online que encanta e fideliza desde o primeiro clique.",
        "pain": [
            "📱 Clientes modernos querem marcar pelo celular, na hora que quiserem",
            "🔄 Processo de agendamento difícil = cliente que não volta",
            "⭐ A experiência do cliente começa antes mesmo de ele chegar no seu negócio",
        ],
        "solution": "O <strong style='color:#fff'>TopAgenda</strong> oferece uma experiência de agendamento simples, elegante e rápida. Seus clientes ficam satisfeitos desde o primeiro contato — e voltam sempre.",
        "cta": "✨ Modernizar meu atendimento",
        "testimonial": "Meus clientes elogiam muito como é fácil marcar. Parece algo de app grande, mas é o meu pequeno negócio. O TopAgenda faz isso por mim.",
    },
    {   # 16 — verde profundo: faturamento previsível
        "accent": "#276749", "bg1": "#06120a", "bg2": "#0b1f12",
        "headline": "Faturamento previsível todo mês com agenda inteligente",
        "sub": "Saiba com antecedência quanto vai faturar na semana — e planeje com segurança.",
        "pain": [
            "📉 Faturamento irregular que sobe e desce sem você entender por quê",
            "🤷 Impossível planejar o negócio sem saber quantos clientes virão",
            "💼 Sem dados, você trabalha no escuro — sem poder tomar decisões melhores",
        ],
        "solution": "Com a agenda organizada e clientes confirmados, você consegue planejar melhor. O <strong style='color:#fff'>TopAgenda</strong> transforma caos em previsibilidade — relatórios, métricas e histórico em tempo real.",
        "cta": "📊 Organizar meu faturamento",
        "testimonial": "Agora consigo prever meu faturamento da semana com dois dias de antecedência. Isso mudou completamente minha gestão financeira.",
    },
    {   # 17 — carvão: profissionalizar
        "accent": "#4A5568", "bg1": "#0a0c0f", "bg2": "#141720",
        "headline": "Profissionalize seu atendimento hoje mesmo",
        "sub": "A primeira impressão define se o cliente volta — ou nunca mais aparece.",
        "pain": [
            "👔 Negócios sem sistema profissional transmitem improviso e insegurança",
            "📋 Caderno e anotações manuais aumentam o risco de erro e confusão",
            "🏅 Clientes pagam mais por negócios que transmitem profissionalismo",
        ],
        "solution": "Um sistema de agendamento profissional mostra que você se importa com a experiência do cliente. Com o <strong style='color:#fff'>TopAgenda</strong>, cada detalhe é pensado para encantar e fidelizar.",
        "cta": "🏆 Profissionalizar agora",
        "testimonial": "Clientes comentam que meu salão parece uma franquia grande. É só impressão — mas é uma impressão que faz eles voltarem e indicarem.",
    },
    {   # 18 — bordô: conversão
        "accent": "#9B2C2C", "bg1": "#150808", "bg2": "#220e0e",
        "headline": "Transforme curiosos em clientes confirmados",
        "sub": "Facilidade de marcar horário = mais conversões para o seu negócio.",
        "pain": [
            "🔍 Muita gente te encontra mas não converte em cliente por dificuldade de agendar",
            "💨 A fricção no processo de marcação faz interessados desistirem",
            "📊 Você poderia ter o dobro de clientes com o mesmo tráfego que já tem",
        ],
        "solution": "Quando é fácil marcar horário, mais pessoas marcam. O <strong style='color:#fff'>TopAgenda</strong> remove as barreiras e transforma visitantes em clientes agendados — automaticamente, sem esforço da sua parte.",
        "cta": "🎯 Aumentar minhas conversões",
        "testimonial": "Antes de 100 pessoas que me achavam, talvez 20 marcavam. Hoje são mais de 60. Só melhorei a facilidade de agendar — e o faturamento disparou.",
    },
    {   # 19 — azul céu: experiência encantadora
        "accent": "#2B6CB0", "bg1": "#050c17", "bg2": "#091525",
        "headline": "A agenda online que seus clientes vão adorar usar",
        "sub": "Simples para você configurar. Incrível para eles usar.",
        "pain": [
            "😕 Sistemas complicados que você mesmo tem dificuldade de usar",
            "📖 Configurações técnicas que ninguém tem paciência de aprender",
            "🤝 Você precisa de uma solução que funcione — não de outro problema",
        ],
        "solution": "O <strong style='color:#fff'>TopAgenda</strong> foi desenvolvido para ser intuitivo e bonito. Você configura em minutos, seus clientes adoram a facilidade — e você fica com mais tempo para o que importa.",
        "cta": "👀 Ver a experiência do cliente",
        "testimonial": "Configurei em 20 minutos sem precisar de suporte. No mesmo dia já tinha clientes agendando. A simplicidade é o maior diferencial.",
    },
    {   # 20 — âmbar escuro: teste grátis
        "accent": "#C05621", "bg1": "#150c05", "bg2": "#25150a",
        "headline": "Teste grátis por 7 dias — sem cartão de crédito",
        "sub": "Experimente sem risco e veja a diferença na prática.",
        "pain": [
            "🤔 Ainda não tem certeza se vale a pena? Totalmente compreensível",
            "💳 Sem compromisso, sem cobrança, sem pegadinha — só resultado",
            "⏱️ Em 7 dias você vai ver agendamentos entrando sozinhos no seu negócio",
        ],
        "solution": "Não estamos pedindo compromisso. Experimente o <strong style='color:#fff'>TopAgenda</strong> gratuitamente por 7 dias e veja como sua agenda pode se transformar. Sem risco, sem complicação — só ganho.",
        "cta": "🎁 Começar teste gratuito",
        "testimonial": "Comecei no teste grátis sem acreditar muito. No terceiro dia já tinha 8 agendamentos novos. Assinou no quinto dia. Não tem como não assinar.",
    },
]

assert len(SUBJECTS) == 20, "Deve haver exatamente 20 assuntos"
assert len(VARIANTS) == 20, "Deve haver exatamente 20 variantes"


def render_template(
    variant_id: int,
    company_name: str = "",
    tracking_pixel_url: str = "",
    click_url: str = "https://topagenda.online",
) -> str:
    """Renderiza o template HTML para a variante dada (1-20)."""
    v = VARIANTS[(variant_id - 1) % 20]
    accent   = v["accent"]
    bg1      = v["bg1"]
    bg2      = v["bg2"]
    headline = v["headline"]
    sub      = v["sub"]
    pain     = v["pain"]
    solution = v["solution"]
    cta      = v["cta"]
    testimonial = v["testimonial"]


    pain_rows = "".join(
        f"""<tr>
          <td style="background:#1a1a2a;border-left:4px solid {accent};border-radius:0 10px 10px 0;padding:14px 18px;margin-bottom:8px;">
            <p style="margin:0;font-size:15px;color:#e2e8f0;line-height:1.5;">{item}</p>
          </td>
        </tr><tr><td style="height:8px;"></td></tr>"""
        for item in pain
    )

    tracking_pixel = f'<img src="{tracking_pixel_url}" width="1" height="1" style="display:none;border:0;" alt="" />' if tracking_pixel_url else ""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <title>TopAgenda</title>
</head>
<body style="margin:0;padding:0;background-color:#0a0a0a;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">

  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#0a0a0a;">
    <tr>
      <td align="center" style="padding:40px 16px;">
        <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="max-width:600px;width:100%;">

          <!-- LOGO -->
          <tr>
            <td align="center" style="padding:0 0 28px 0;">
              <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                <tr>
                  <td style="background:{accent};border-radius:14px;padding:12px 26px;">
                    <span style="font-size:20px;font-weight:800;color:#ffffff;letter-spacing:-0.5px;">✂️ TopAgenda</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- HERO -->
          <tr>
            <td style="background:linear-gradient(160deg,{bg1} 0%,{bg2} 100%);border-radius:20px 20px 0 0;padding:44px 40px 36px;border:1px solid #222;border-bottom:none;">
              <h1 style="margin:0 0 16px;font-size:30px;font-weight:900;color:#ffffff;line-height:1.25;">{headline}</h1>
              <p style="margin:0;font-size:16px;color:#94a3b8;line-height:1.7;">{sub}</p>
            </td>
          </tr>

          <!-- DOR -->
          <tr>
            <td style="background:{bg2};padding:0 40px 32px;border:1px solid #222;border-top:none;border-bottom:none;">
              <p style="margin:24px 0 16px;font-size:15px;color:#e2e8f0;font-weight:700;">Isso soa familiar?</p>
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                {pain_rows}
              </table>
            </td>
          </tr>

          <!-- SOLUÇÃO -->
          <tr>
            <td style="background:{bg1};padding:32px 40px;border:1px solid #222;border-top:2px solid {accent};border-bottom:none;">
              <p style="margin:0 0 6px;font-size:12px;font-weight:700;color:{accent};letter-spacing:2px;text-transform:uppercase;">A solução</p>
              <p style="margin:0;font-size:16px;color:#cbd5e0;line-height:1.75;">{solution}</p>
            </td>
          </tr>

          <!-- FEATURES -->
          <tr>
            <td style="background:{bg1};padding:0 40px 32px;border:1px solid #222;border-top:none;border-bottom:none;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                <tr><td style="padding:0 0 12px;"><table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"><tr>
                  <td width="36" valign="top"><div style="background:rgba(255,255,255,0.08);border-radius:8px;width:32px;height:32px;text-align:center;line-height:32px;font-size:16px;">📅</div></td>
                  <td valign="middle" style="padding-left:12px;"><p style="margin:0;font-size:14px;color:#e2e8f0;"><strong style="color:#fff;">Agendamento online 24/7</strong> — Clientes agendam a qualquer hora</p></td>
                </tr></table></td></tr>
                <tr><td style="padding:0 0 12px;"><table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"><tr>
                  <td width="36" valign="top"><div style="background:rgba(255,255,255,0.08);border-radius:8px;width:32px;height:32px;text-align:center;line-height:32px;font-size:16px;">💬</div></td>
                  <td valign="middle" style="padding-left:12px;"><p style="margin:0;font-size:14px;color:#e2e8f0;"><strong style="color:#fff;">Lembretes automáticos</strong> — Chega de cliente faltando sem avisar</p></td>
                </tr></table></td></tr>
                <tr><td style="padding:0 0 12px;"><table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"><tr>
                  <td width="36" valign="top"><div style="background:rgba(255,255,255,0.08);border-radius:8px;width:32px;height:32px;text-align:center;line-height:32px;font-size:16px;">📊</div></td>
                  <td valign="middle" style="padding-left:12px;"><p style="margin:0;font-size:14px;color:#e2e8f0;"><strong style="color:#fff;">Relatórios em tempo real</strong> — Saiba exatamente quanto está ganhando</p></td>
                </tr></table></td></tr>
                <tr><td><table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"><tr>
                  <td width="36" valign="top"><div style="background:rgba(255,255,255,0.08);border-radius:8px;width:32px;height:32px;text-align:center;line-height:32px;font-size:16px;">👥</div></td>
                  <td valign="middle" style="padding-left:12px;"><p style="margin:0;font-size:14px;color:#e2e8f0;"><strong style="color:#fff;">Histórico completo</strong> — Serviços, datas e preferências de cada cliente</p></td>
                </tr></table></td></tr>
              </table>
            </td>
          </tr>

          <!-- DEPOIMENTO -->
          <tr>
            <td style="background:{bg2};padding:28px 40px;border:1px solid #222;border-top:none;border-bottom:none;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                <tr>
                  <td style="background:rgba(255,255,255,0.04);border-radius:12px;padding:20px;border-left:4px solid {accent};">
                    <p style="margin:0 0 10px;font-size:22px;">⭐⭐⭐⭐⭐</p>
                    <p style="margin:0 0 12px;font-size:14px;color:#cbd5e0;line-height:1.7;font-style:italic;">"{testimonial}"</p>
                    <p style="margin:0;font-size:13px;color:{accent};font-weight:700;">— Cliente TopAgenda</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- CTA -->
          <tr>
            <td style="background:{bg1};border-radius:0 0 20px 20px;padding:36px 40px;border:1px solid #222;border-top:2px solid {accent};text-align:center;">
              <p style="margin:0 0 8px;font-size:20px;font-weight:900;color:#ffffff;">Seu painel está esperando por você.</p>
              <p style="margin:0 0 28px;font-size:14px;color:#94a3b8;">Clique abaixo e transforme sua agenda em segundos.</p>
              <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center">
                <tr>
                  <td style="border-radius:12px;background:{accent};box-shadow:0 6px 24px rgba(0,0,0,0.4);">
                    <a href="{click_url}" target="_blank"
                      style="display:inline-block;padding:16px 44px;font-size:16px;font-weight:800;color:#ffffff;text-decoration:none;">
                      {cta}
                    </a>
                  </td>
                </tr>
              </table>
              <p style="margin:20px 0 0;font-size:13px;color:#475569;">
                Não tem conta?
                <a href="https://topagenda.online/register" style="color:{accent};text-decoration:underline;">Crie grátis em 2 minutos</a>
              </p>
            </td>
          </tr>

          <!-- FOOTER -->
          <tr>
            <td style="padding:28px 40px 0;text-align:center;">
              <p style="margin:0 0 6px;font-size:12px;color:#4a5568;">© 2026 TopAgenda — Agendamento online profissional</p>
              <p style="margin:0;font-size:11px;color:#2d3748;">
                Você recebeu este email pois seu negócio foi encontrado em nossa pesquisa. &nbsp;|&nbsp;
                <a href="https://topagenda.online/unsubscribe" style="color:#6366f1;text-decoration:none;">Cancelar inscrição</a>
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>

  {tracking_pixel}
</body>
</html>"""
