from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':390,'height':844},reduced_motion='reduce')
    page.goto('http://127.0.0.1:8765/')
    page.evaluate('''() => {
      document.getElementById('root').remove();document.body.style.margin='0';
      const panel=document.createElement('ha-finance-panel');
      const data={deposits:[],workers:[{id:'w',name:'Миша',employment:'TK',income:17400000,advance_day:29,salary_day:14}],budgets:[{id:'b',name:'Ноябрь 2026',month:'2026-11',expenses:[]}]};
      const estimate={salary:9570000,advance:8700000,salary_date:'2026-11-13',advance_date:'2026-11-27',workdays:20,first_workdays:9,second_workdays:11,salary_period:'2026-10',advance_period:'2026-11'};
      window.pending=[];
      panel.hass={connection:{subscribeMessage:async cb=>()=>{}},callWS:msg=>new Promise(resolve=>window.pending.push(()=>resolve(msg.type==='ha_finance/get'?data:msg.type==='ha_finance/budget_schedule'?[]:estimate)))};
      document.body.append(panel);
    }''')
    panel=page.locator('ha-finance-panel')
    expect(panel.locator('.skeleton-cards')).to_be_visible()
    assert panel.locator('.skeleton-line').first.evaluate('el=>getComputedStyle(el).animationName')=='none'
    page.evaluate('window.pending.shift()()')
    expect(panel.locator('.skeleton-cards')).to_have_count(0)
    panel.get_by_role('button',name='Открыть разделы финансов').click()
    panel.get_by_role('button',name='Заработная плата',exact=True).click()
    expect(panel.locator('.skeleton-preview')).to_be_visible()
    page.evaluate('window.pending.shift()()')
    expect(panel.locator('.skeleton-preview')).to_have_count(0)
    panel.get_by_role('button',name='Миша',exact=True).click()
    expect(panel.locator('.skeleton-payments')).to_be_visible()
    page.evaluate('window.pending.shift()()')
    expect(panel.locator('.salary-payments')).to_be_visible()
    panel.get_by_role('button',name='Все работники').click()
    panel.get_by_role('button',name='Открыть разделы финансов').click()
    panel.get_by_role('button',name='Распределение бюджета',exact=True).click()
    panel.get_by_role('button',name='Ноябрь 2026',exact=True).click()
    expect(panel.locator('.skeleton-periods')).to_be_visible()
    page.evaluate('window.pending.splice(0).forEach(f=>f())')
    expect(panel.locator('.budget-periods')).to_be_visible()
    expect(panel.locator('.skeleton')).to_have_count(0)
    browser.close()
    print('PASS: delayed initial data, payroll preview/detail, budget period skeletons, replacement after response, reduced motion')
