"""UI regression checks; same server/Playwright prerequisites as browser_panel.py."""
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':390,'height':844})
    page.goto('http://127.0.0.1:8765/')
    page.evaluate('''() => {
      document.getElementById('root').remove();document.body.style.margin='0';
      const panel=document.createElement('ha-finance-panel');let cb;
      const data={deposits:[{id:'home',name:'Вклад озон',principal:29000000,expenses:[{id:'mortgage',name:'Ипотека',amount:4700000,date:'2026-11-08',paid:false},...Array.from({length:18},(_,i)=>({id:'e'+i,name:'Платёж '+i,amount:0,date:'2027-01-01',paid:false}))]}]};
      window.calls=[];
      panel.hass={connection:{subscribeMessage:async callback=>{cb=callback;cb(structuredClone(data));return ()=>{}}},callWS:async msg=>{if(msg.type==='ha_finance/mutate'){window.calls.push(msg);if(msg.action==='expense_delete')data.deposits[0].expenses=data.deposits[0].expenses.filter(e=>e.id!==msg.payload.expense_id);if(msg.action==='expense_save')data.deposits[0].expenses.push({...msg.payload,id:'income'});if(msg.action==='expense_paid')data.deposits[0].expenses.find(e=>e.id===msg.payload.expense_id).paid=msg.payload.paid;if(msg.action==='delete')data.deposits=[];cb(structuredClone(data))}return structuredClone(data)}};
      document.body.append(panel);
    }''')
    panel=page.locator('ha-finance-panel')
    card=panel.locator('.card')
    expect(card).to_contain_text('Свободные деньги')
    assert card.locator('.metric').first.inner_text().replace('\xa0','').find('243000')>=0
    expect(card).to_contain_text('Оплачено')
    expect(card).to_contain_text('Ожидается')
    panel.get_by_role('button',name='Действия: Вклад озон',exact=True).click()
    expect(panel.get_by_role('dialog',name='Вклад озон',exact=True).get_by_role('button',name='Удалить',exact=True)).to_be_visible()
    expect(panel.get_by_role('heading',name='Мои вклады')).to_be_visible()
    panel.get_by_role('dialog',name='Вклад озон',exact=True).get_by_role('button',name='Удалить',exact=True).click()
    expect(panel.get_by_role('dialog',name='Удалить вклад?')).to_be_visible()
    panel.get_by_role('dialog',name='Удалить вклад?').get_by_role('button',name='Отмена',exact=True).click()
    assert page.evaluate('window.calls.length')==0
    card.click(button='right')
    panel.get_by_role('dialog',name='Вклад озон',exact=True).get_by_role('button',name='Изменить',exact=True).click()
    expect(panel.get_by_role('dialog',name='Изменить вклад').get_by_label('Название',exact=True)).to_have_value('Вклад озон')
    panel.get_by_role('button',name='Закрыть',exact=True).click()
    card.click()
    page.go_back()
    expect(panel.get_by_role('heading',name='Мои вклады')).to_be_visible()
    page.go_forward()
    expect(panel.locator('.toolbar h1')).to_have_text('Вклад озон')
    def swipe(x1,y1,x2,y2):
        panel.locator('main').evaluate('''(el,p) => {
          const touch=(x,y)=>new Touch({identifier:1,target:el,clientX:x,clientY:y});
          el.dispatchEvent(new TouchEvent('touchstart',{bubbles:true,touches:[touch(p[0],p[1])]}));
          el.dispatchEvent(new TouchEvent('touchmove',{bubbles:true,cancelable:true,touches:[touch(p[2],p[3])]}));
          el.dispatchEvent(new TouchEvent('touchend',{bubbles:true,changedTouches:[touch(p[2],p[3])]}));
        }''',[x1,y1,x2,y2])
    swipe(10,200,15,400)
    expect(panel.locator('.toolbar h1')).to_have_text('Вклад озон')
    swipe(10,200,140,205)
    expect(panel.get_by_role('heading',name='Мои вклады')).to_be_visible()
    card.click()
    expect(panel.locator('.toolbar h1')).to_have_text('Вклад озон')
    metrics=panel.locator('.summary .metric')
    assert metrics.count()==4
    assert len({round(m.bounding_box()['y']) for m in metrics.all()})==2
    assert metrics.first.locator('strong').evaluate('el=>parseFloat(getComputedStyle(el).fontSize)')>=21
    header=panel.locator('.deposit-toolbar').bounding_box()
    title=panel.locator('.deposit-toolbar .toolbar-title').bounding_box()
    assert abs((title['x']+title['width']/2)-(header['x']+header['width']/2))<1
    expect(panel.get_by_text('Куда пойдут деньги')).to_have_count(0)
    expect(panel.get_by_role('button',name='Удалить вклад',exact=True)).to_have_count(0)
    panel.get_by_role('button',name='Действия со вкладом').click()
    sheet=panel.get_by_role('dialog',name='Вклад озон',exact=True)
    expect(sheet.get_by_role('button',name='Пополнить',exact=True)).to_have_count(0)
    sheet.get_by_role('button',name='Закрыть действия').click()
    panel.get_by_role('button',name='Действия с операцией Ипотека').click()
    sheet=panel.get_by_role('dialog',name='Ипотека',exact=True)
    sheet.get_by_role('button',name='Изменить',exact=True).click()
    expect(panel.get_by_label('Название',exact=True)).to_have_value('Ипотека')
    panel.get_by_role('button',name='Закрыть',exact=True).click()
    page.on('dialog',lambda d:d.accept())
    panel.get_by_role('button',name='Действия с операцией Ипотека').click()
    panel.get_by_role('dialog',name='Ипотека',exact=True).get_by_role('button',name='Удалить',exact=True).click()
    panel.get_by_role('dialog',name='Точно удалить?').get_by_role('button',name='Удалить',exact=True).click()
    expect(panel.get_by_role('button',name='Действия с операцией Ипотека')).to_have_count(0)
    assert page.evaluate('window.calls.at(-1).action')=='expense_delete'
    page.evaluate('window.scrollTo(0,document.documentElement.scrollHeight)')
    last=panel.locator('.expense').last
    last.scroll_into_view_if_needed()
    assert abs(panel.locator('.toolbar').bounding_box()['y'])<1
    dock=panel.locator('.expense-dock')
    assert last.bounding_box()['y']+last.bounding_box()['height'] <= dock.bounding_box()['y']
    expect(dock.get_by_role('button',name='Добавить',exact=True)).to_be_in_viewport()
    dock.get_by_role('button',name='Добавить',exact=True).click()
    expect(panel.get_by_role('dialog',name='Добавить',exact=True)).to_be_visible()
    panel.get_by_role('button',name='Закрыть',exact=True).click()
    dock.get_by_role('button',name='Добавить',exact=True).click()
    dialog=panel.get_by_role('dialog',name='Добавить',exact=True)
    dialog.get_by_role('radio',name='Доход',exact=True).check()
    dialog.get_by_label('Название',exact=True).fill('Зарплата')
    dialog.get_by_label('Сумма, ₽',exact=True).fill('10000')
    dialog.get_by_label('Уже получено',exact=True).check()
    dialog.get_by_role('button',name='Сохранить',exact=True).click()
    income=panel.locator('.expense').filter(has_text='Зарплата')
    expect(income).to_contain_text('+10')
    expect(income.get_by_role('button',name='Действия с операцией Зарплата')).to_have_count(0)
    expect(panel.locator('.donut')).to_contain_text('300')
    income.get_by_role('button',name='Удалить операцию Зарплата').click()
    confirmation=panel.get_by_role('dialog',name='Точно удалить?')
    confirmation.get_by_role('button',name='Отмена').click()
    expect(income).to_be_visible()
    income.get_by_role('button',name='Удалить операцию Зарплата').click()
    panel.get_by_role('dialog',name='Точно удалить?').get_by_role('button',name='Удалить',exact=True).click()
    expect(panel.locator('.donut')).to_contain_text('290')
    expect(income).to_have_count(0)
    page.evaluate('window.scrollTo(0,0)')
    page.screenshot(path='/tmp/finance-deposit.png',full_page=False)
    panel.get_by_role('button',name='Действия со вкладом').click()
    panel.get_by_role('dialog',name='Вклад озон',exact=True).get_by_role('button',name='Удалить вклад').click()
    expect(panel.get_by_role('heading',name='Мои вклады')).to_be_visible()
    assert page.evaluate('window.calls.at(-1).action')=='delete'
    browser.close()
    print('PASS: card totals, deposit header, action sheets, expense edit/delete, pinned add button, last row clearance, deposit deletion')
