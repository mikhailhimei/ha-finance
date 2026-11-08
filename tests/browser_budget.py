from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':390,'height':844})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8765/')
    page.evaluate('''() => {
      document.getElementById('root').remove();document.body.style.margin='0';
      const panel=document.createElement('ha-finance-panel');let cb;
      const data={deposits:[],workers:[],budgets:[]};
      panel.hass={connection:{subscribeMessage:async c=>{cb=c;c(structuredClone(data));return ()=>{}}},callWS:async msg=>{
        if(msg.type==='ha_finance/budget_schedule')return [{id:'w:salary',name:'Миша · Зарплата',date:'2026-11-13',amount:10000000},{id:'f:fixed',name:'Аренда',date:'2026-11-06',amount:3000000}];
        if(msg.type==='ha_finance/mutate'){
          if(msg.action==='budget_create')data.budgets.push({id:'b',name:'Ноябрь 2026',month:msg.payload.month,expenses:[]});
          if(msg.action==='budget_expense_save')data.budgets[0].expenses.push({...msg.payload,id:'e'});
          if(msg.action==='budget_delete')data.budgets=[];if(msg.action==='budget_expense_delete')data.budgets[0].expenses=[];
          cb(structuredClone(data));
        }return structuredClone(data);
      }};document.body.append(panel);
    }''')
    panel=page.locator('ha-finance-panel')
    panel.get_by_role('button',name='Открыть разделы финансов').click()
    panel.get_by_role('button',name='Распределение бюджета',exact=True).click()
    panel.get_by_role('button',name='Создать бюджет',exact=True).click()
    panel.get_by_label('Месяц и год',exact=True).fill('2026-11')
    panel.get_by_role('button',name='Сохранить',exact=True).click()
    panel.locator('.card').click()
    expect(panel.locator('.toolbar')).to_have_count(1)
    expect(panel.locator('.toolbar h1')).to_have_text('Ноябрь 2026')
    expect(panel.get_by_label('Месяц выплат',exact=True)).to_have_count(0)
    expect(panel.locator('.budget-periods button').first).to_contain_text('Посмотреть общий')
    panel.locator('.budget-periods button').filter(has_text='Миша').click()
    panel.get_by_role('button',name='Добавить трату',exact=True).click()
    panel.get_by_label('Наименование',exact=True).fill('Здоровье')
    panel.get_by_label('Сумма, ₽',exact=True).fill('11000')
    panel.get_by_label('Комментарий',exact=True).fill('Стоматолог')
    panel.get_by_role('button',name='Сохранить',exact=True).click()
    expect(panel.locator('.budget-expenses')).to_contain_text('Стоматолог')
    expect(panel.locator('.summary .metric').last).to_contain_text('89')
    panel.locator('.budget-periods button').first.click()
    expect(panel.locator('.summary .metric').last).to_contain_text('119')
    panel.get_by_role('button',name='Действия с тратой Здоровье').click()
    panel.get_by_role('dialog',name='Здоровье',exact=True).get_by_role('button',name='Удалить',exact=True).click()
    expect(panel.locator('.summary .metric').last).to_contain_text('130')
    page.go_back()
    expect(panel.get_by_role('button',name='Создать бюджет',exact=True)).to_be_visible()
    card=panel.get_by_role('button',name='Ноябрь 2026',exact=True)
    bounds=card.bounding_box()
    page.mouse.move(bounds['x']+30,bounds['y']+30)
    page.mouse.down();page.wait_for_timeout(700);page.mouse.up()
    confirmation=panel.get_by_role('dialog',name='Удалить бюджет?',exact=True)
    expect(confirmation).to_contain_text('все его траты')
    confirmation.get_by_role('button',name='Отмена',exact=True).click()
    expect(card).to_be_visible()
    card.click(button='right')
    panel.get_by_role('dialog',name='Удалить бюджет?',exact=True).get_by_role('button',name='Удалить',exact=True).click()
    expect(card).to_have_count(0)
    expect(panel.get_by_role('heading',name='Бюджетов пока нет')).to_be_visible()
    assert not errors,errors
    browser.close()
    print('PASS: budget creation, income periods, expense/comment save, individual and combined balances, deletion, back navigation')
