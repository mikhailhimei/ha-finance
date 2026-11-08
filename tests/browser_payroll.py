"""Payroll and create-deposit bottom-sheet regression tests."""
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
      const data={deposits:[],workers:[]};window.calls=[];
      panel.hass={connection:{subscribeMessage:async callback=>{cb=callback;cb(structuredClone(data));return ()=>{}}},callWS:async msg=>{
        if(msg.type==='ha_finance/payroll')return {workdays:15,first_workdays:5,second_workdays:10,advance:4000000,salary:8000000,advance_date:'2026-12-29',salary_date:'2026-12-14',salary_period:'2026-11',advance_period:'2026-12'};if(msg.type==='ha_finance/mutate'){window.calls.push(msg);const worker={...msg.payload,id:msg.payload.worker_id||'w1'};const i=data.workers.findIndex(w=>w.id===worker.id);if(i<0)data.workers.push(worker);else data.workers[i]=worker;cb(structuredClone(data))}return structuredClone(data)}};
      document.body.append(panel);
    }''')
    panel=page.locator('ha-finance-panel')
    panel.get_by_role('button',name='Создать вклад',exact=True).click()
    sheet=panel.get_by_role('dialog',name='Новый вклад')
    assert abs(sheet.bounding_box()['y']+sheet.bounding_box()['height']-844)<2
    panel.get_by_role('button',name='Закрыть',exact=True).click()
    panel.get_by_role('button',name='Открыть разделы финансов').click()
    panel.get_by_role('button',name='Заработная плата',exact=True).click()
    panel.get_by_role('button',name='Указать работника',exact=True).click()
    sheet=panel.get_by_role('dialog',name='Указать работника')
    expect(sheet.get_by_role('combobox',name='Тип оформления')).to_have_value('TK')
    assert sheet.get_by_role('option').count()==1
    sheet.get_by_label('Наименование',exact=True).fill('Иван')
    sheet.get_by_label('Доход, ₽',exact=True).fill('100000')
    sheet.get_by_label('Число аванса',exact=True).fill('25')
    sheet.get_by_label('Число зарплаты',exact=True).fill('10')
    sheet.get_by_role('button',name='Сохранить',exact=True).click()
    expect(panel.get_by_role('heading',name='Иван',exact=True)).to_be_visible()
    assert page.evaluate('window.calls[0].payload.income')==10000000
    panel.get_by_role('button',name='Изменить работника Иван').click()
    sheet=panel.get_by_role('dialog',name='Изменить работника')
    expect(sheet.get_by_label('Число аванса',exact=True)).to_have_value('25')
    sheet.get_by_label('Доход, ₽',exact=True).fill('120000')
    sheet.get_by_role('button',name='Сохранить',exact=True).click()
    expect(panel.locator('.worker-card')).to_contain_text('120')
    expect(panel.locator('.worker-preview-payments')).to_contain_text('14.12.2026')
    expect(panel.locator('.worker-preview-payments')).to_contain_text('29.12.2026')
    expect(panel.locator('.worker-preview-payments strong')).to_have_count(2)
    panel.get_by_role('button',name='Открыть работника Иван',exact=True).click()
    expect(panel.locator('.toolbar')).to_have_count(1)
    expect(panel.locator('.toolbar h1')).to_have_text('Иван')
    expect(panel.locator('.toolbar').get_by_role('button',name='Все работники')).to_be_visible()
    expect(panel.locator('.toolbar').get_by_role('button',name='Изменить работника Иван')).to_be_visible()
    expect(panel.get_by_label('Месяц выплат',exact=True)).to_be_visible()
    expect(panel.locator('.salary-payments')).to_contain_text('29.12.2026')
    expect(panel.locator('.salary-payments')).to_contain_text('14.12.2026')
    expect(panel.locator('.salary-payments .metric')).to_have_count(2)
    panel.get_by_role('button',name='Все работники',exact=True).click()
    expect(panel.get_by_role('button',name='Указать работника',exact=True)).to_be_visible()
    assert not errors,errors
    browser.close()
    print('PASS: create deposit bottom sheet, worker fields, TK selection, shared save payload, worker rendering and editing')
