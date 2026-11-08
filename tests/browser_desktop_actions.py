from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':1440,'height':900},has_touch=True)
    page=context.new_page()
    page.goto('http://127.0.0.1:8765/')
    page.evaluate('''() => {
      document.getElementById('root').remove();
      const panel=document.createElement('ha-finance-panel');
      const data={deposits:[{id:'d',name:'Вклад',principal:100000,expenses:[]}],workers:[{id:'w',name:'Работник',employment:'TK',income:100000,advance_day:29,salary_day:14}],budgets:[{id:'b',name:'Ноябрь 2026',month:'2026-11',expenses:[]}]};
      panel.hass={connection:{subscribeMessage:async cb=>{cb(data);return ()=>{}}},callWS:async msg=>msg.type==='ha_finance/get'?data:msg.type==='ha_finance/budget_schedule'?[]:{salary:50000,advance:50000,salary_date:'2026-11-13',advance_date:'2026-11-27'}};
      document.body.append(panel);
    }''')
    assert page.evaluate("!matchMedia('(hover:hover) and (pointer:fine)').matches")
    panel=page.locator('ha-finance-panel')
    for section,name in [(None,'Вклад'),('Заработная плата','Работник'),('Распределение бюджета','Ноябрь 2026')]:
        if section:
            panel.get_by_role('button',name='Открыть разделы финансов').click()
            panel.get_by_role('button',name=section,exact=True).click()
        pencil=panel.get_by_role('button',name=f'Действия: {name}',exact=True)
        expect(pencil).to_be_visible()
        pencil.click()
        dialog=panel.get_by_role('dialog',name=name,exact=True)
        expect(dialog.get_by_role('button',name='Удалить',exact=True)).to_be_visible()
        box=dialog.bounding_box()
        assert box['y']>100 and box['y']+box['height']<850
        dialog.get_by_role('button',name='Отмена',exact=True).click()
    browser.close()
    print('PASS: visible pencils and centered action dialogs for deposits, workers and budgets on a touch-enabled desktop')
