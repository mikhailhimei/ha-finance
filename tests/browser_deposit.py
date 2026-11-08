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
      panel.hass={connection:{subscribeMessage:async callback=>{cb=callback;cb(structuredClone(data));return ()=>{}}},callWS:async msg=>{if(msg.type==='ha_finance/mutate'){window.calls.push(msg);if(msg.action==='expense_delete')data.deposits[0].expenses=data.deposits[0].expenses.filter(e=>e.id!==msg.payload.expense_id);if(msg.action==='delete')data.deposits=[];cb(structuredClone(data))}return structuredClone(data)}};
      document.body.append(panel);
    }''')
    panel=page.locator('ha-finance-panel')
    card=panel.locator('.card')
    expect(card).to_contain_text('Свободно после всех планов')
    assert card.locator('.metric').first.inner_text().replace('\xa0','').find('243000')>=0
    expect(card).not_to_contain_text('Оплачено')
    expect(card).not_to_contain_text('Ожидается')
    card.click()
    expect(panel.locator('.toolbar h1')).to_have_text('Вклад озон')
    expect(panel.get_by_text('Куда пойдут деньги')).to_have_count(0)
    expect(panel.get_by_role('button',name='Удалить вклад',exact=True)).to_have_count(0)
    panel.get_by_role('button',name='Действия со вкладом').click()
    sheet=panel.get_by_role('dialog',name='Вклад озон',exact=True)
    expect(sheet.get_by_role('button',name='Пополнить',exact=True)).to_be_visible()
    sheet.get_by_role('button',name='Пополнить',exact=True).click()
    expect(panel.get_by_role('dialog',name='Пополнить вклад')).to_be_visible()
    panel.get_by_role('button',name='Закрыть',exact=True).click()
    panel.get_by_role('button',name='Действия с расходом Ипотека').click()
    sheet=panel.get_by_role('dialog',name='Ипотека',exact=True)
    sheet.get_by_role('button',name='Изменить',exact=True).click()
    expect(panel.get_by_label('Название',exact=True)).to_have_value('Ипотека')
    panel.get_by_role('button',name='Закрыть',exact=True).click()
    page.on('dialog',lambda d:d.accept())
    panel.get_by_role('button',name='Действия с расходом Ипотека').click()
    panel.get_by_role('dialog',name='Ипотека',exact=True).get_by_role('button',name='Удалить',exact=True).click()
    expect(panel.get_by_role('button',name='Действия с расходом Ипотека')).to_have_count(0)
    assert page.evaluate('window.calls.at(-1).action')=='expense_delete'
    page.evaluate('window.scrollTo(0,document.documentElement.scrollHeight)')
    last=panel.locator('.expense').last
    last.scroll_into_view_if_needed()
    dock=panel.locator('.expense-dock')
    assert last.bounding_box()['y']+last.bounding_box()['height'] <= dock.bounding_box()['y']
    expect(dock.get_by_role('button',name='Добавить расход')).to_be_in_viewport()
    dock.get_by_role('button',name='Добавить расход').click()
    expect(panel.get_by_role('dialog',name='Новый расход')).to_be_visible()
    panel.get_by_role('button',name='Закрыть',exact=True).click()
    page.evaluate('window.scrollTo(0,0)')
    page.screenshot(path='/tmp/finance-deposit.png',full_page=False)
    panel.get_by_role('button',name='Действия со вкладом').click()
    panel.get_by_role('dialog',name='Вклад озон',exact=True).get_by_role('button',name='Удалить вклад').click()
    expect(panel.get_by_role('heading',name='Мои вклады')).to_be_visible()
    assert page.evaluate('window.calls.at(-1).action')=='delete'
    browser.close()
    print('PASS: card totals, deposit header, action sheets, expense edit/delete, pinned add button, last row clearance, deposit deletion')
