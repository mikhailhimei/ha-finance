"""Run with Playwright installed and built assets served on 127.0.0.1:8765."""
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    page = browser.new_page(viewport={'width':390, 'height':844})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    # Block external styles: the actual HA panel must carry its own CSS.
    page.route('**/*.css', lambda route: route.abort())
    page.goto('http://127.0.0.1:8765/')
    page.evaluate('''() => {
      document.getElementById('root').remove();
      const host = document.createElement('div');
      const shadow = host.attachShadow({mode:'open'});
      const panel = document.createElement('ha-finance-panel');
      panel.hass = {callWS:async msg=>msg.type==='ha_finance/budget_schedule'?[]:({deposits:[]}), connection:{subscribeMessage:async cb=>{cb({deposits:[]});return ()=>{}}}};
      window.menuEvents=0;
      document.addEventListener('hass-toggle-menu',()=>window.menuEvents++);
      shadow.append(panel); document.body.style.margin='0';document.body.append(host);
    }''')
    panel = page.locator('ha-finance-panel')
    panel.get_by_role('heading', name='Мои вклады', exact=True).wait_for()
    assert panel.locator('.finance').evaluate("el=>getComputedStyle(el).backgroundColor") == 'rgb(246, 248, 245)'
    panel.get_by_role('button',name='Открыть меню Home Assistant').click()
    assert page.evaluate('window.menuEvents') == 1
    panel.get_by_role('button',name='Открыть разделы финансов').click()
    menu = panel.get_by_role('dialog',name='Разделы финансов')
    assert menu.bounding_box()['y'] > 400
    menu.get_by_role('button',name='Распределение бюджета').click()
    panel.get_by_role('heading',name='Распределение бюджета',exact=True,level=1).wait_for()
    expect(menu).to_have_count(0)
    panel.get_by_role('button',name='Открыть разделы финансов').click()
    page.keyboard.press('Escape')
    expect(menu).to_have_count(0)
    page.set_viewport_size({'width':1280,'height':900})
    panel.get_by_role('button',name='Открыть разделы финансов').click()
    assert menu.bounding_box()['y'] < 150
    menu.get_by_role('button',name='Учёт использования вкладов').click()
    panel.get_by_role('button',name='Создать вклад',exact=True).click()
    dialog=panel.get_by_role('dialog',name='Новый вклад')
    assert dialog.locator('..').evaluate("el=>getComputedStyle(el).position") == 'fixed'
    panel.get_by_role('button',name='Закрыть',exact=True).click()
    page.set_viewport_size({'width':390,'height':844})
    panel.get_by_role('button',name='Открыть разделы финансов').click()
    expect(menu).to_be_visible()
    page.screenshot(path='/tmp/ha-finance-menu.png', animations='disabled')
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors, errors
    browser.close()
    print('PASS: built bundle, nested Shadow DOM styles without external CSS, composed HA menu event, mobile sheet, desktop menu, tab selection, Escape, styled modal, mobile overflow')
