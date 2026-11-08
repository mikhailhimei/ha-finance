from playwright.sync_api import sync_playwright, expect
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':390,'height':844})
    page.goto('http://127.0.0.1:8765/')
    page.evaluate('''() => {
      document.getElementById('root').remove();document.body.style.margin='0';
      const panel=document.createElement('ha-finance-panel');let cb;const data={deposits:[],debts:[]};
      panel.hass={connection:{subscribeMessage:async c=>{cb=c;c(data);return ()=>{}}},callWS:async msg=>{
        if(msg.type==='ha_finance/mutate'){
          if(msg.action==='debt_create')data.debts.push({...msg.payload,remaining:msg.payload.principal,id:'d',payments:[]});
          if(msg.action==='debt_delete')data.debts=[];if(msg.action==='debt_update'){const debt=data.debts[0],paid=debt.principal-debt.remaining;Object.assign(debt,msg.payload,{remaining:msg.payload.principal-paid})}if(msg.action==='debt_payment_delete'){const debt=data.debts[0],payment=debt.payments.find(p=>p.id===msg.payload.payment_id);debt.remaining+=payment.amount;debt.payments=debt.payments.filter(p=>p.id!==payment.id)}if(msg.action==='debt_payment'){data.debts[0].remaining-=msg.payload.amount;data.debts[0].payments.push({...msg.payload,id:'p'})}cb(structuredClone(data));
        }return structuredClone(data);
      }};document.body.append(panel);
    }''')
    panel=page.locator('ha-finance-panel')
    panel.get_by_role('button',name='Открыть разделы финансов').click()
    menu=panel.get_by_role('dialog',name='Разделы финансов')
    expect(menu.locator('nav button').nth(3)).to_contain_text('Заработная плата')
    panel.get_by_role('button',name='Долги',exact=True).click()
    panel.get_by_role('button',name='Создать долг',exact=True).click()
    panel.get_by_label('Наименование',exact=True).fill('Кредит')
    panel.get_by_label('Изначальная сумма, ₽',exact=True).fill('100000')
    expect(panel.get_by_label('Текущий остаток, ₽',exact=True)).to_have_count(0)
    panel.get_by_role('button',name='Сохранить',exact=True).click()
    panel.locator('.card').click()
    expect(panel.locator('.toolbar h1')).to_have_text('Кредит')
    panel.get_by_role('button',name='Добавить',exact=True).click()
    dialog=panel.get_by_role('dialog',name='Внести платёж',exact=True)
    expect(dialog.locator('input')).to_have_count(1)
    box=dialog.bounding_box();assert abs(box['y']+box['height']-844)<2
    dialog.get_by_label('Внесённая сумма, ₽',exact=True).fill('10000')
    dialog.get_by_role('button',name='Сохранить',exact=True).click()
    expect(panel.locator('.debt-summary .metric').first).to_contain_text('90')
    expect(panel.locator('.debt-summary .metric').last).to_contain_text('100')
    expect(panel.locator('.debt-payments')).to_contain_text('10')
    metrics=panel.locator('.debt-summary .metric')
    assert metrics.nth(1).bounding_box()['y']>metrics.nth(0).bounding_box()['y']+metrics.nth(0).bounding_box()['height']
    panel.locator('.debt-payments').get_by_role('button',name=__import__('re').compile('Удалить платёж')).click()
    panel.get_by_role('dialog',name='Удалить платёж?',exact=True).get_by_role('button',name='Удалить',exact=True).click()
    expect(panel.locator('.debt-summary .metric').first).to_contain_text('100')
    expect(panel.locator('.debt-payments')).to_have_count(0)
    page.go_back()
    expect(panel.get_by_role('button',name='Создать долг',exact=True)).to_be_visible()
    card=panel.get_by_role('button',name='Кредит',exact=True)
    card.dispatch_event('pointerdown',{'pointerType':'touch','isPrimary':True,'button':0,'clientX':50,'clientY':100})
    page.wait_for_timeout(700)
    card.dispatch_event('pointerup',{'pointerType':'touch'})
    panel.get_by_role('dialog',name='Кредит',exact=True).get_by_role('button',name='Редактировать',exact=True).click()
    panel.get_by_label('Наименование',exact=True).fill('Банк')
    panel.get_by_role('button',name='Сохранить',exact=True).click()
    expect(panel.get_by_role('button',name='Банк',exact=True)).to_be_visible()
    panel.get_by_role('button',name='Банк',exact=True).click(button='right')
    panel.get_by_role('dialog',name='Банк',exact=True).get_by_role('button',name='Удалить',exact=True).click()
    panel.get_by_role('dialog',name='Удалить долг?',exact=True).get_by_role('button',name='Удалить',exact=True).click()
    expect(panel.get_by_role('heading',name='Долгов пока нет')).to_be_visible()
    browser.close();print('PASS: debt creation, detail header, mobile payment sheet with one field, repayment and history, back')
