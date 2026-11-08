from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':900})
    page.goto('http://127.0.0.1:8765/')
    button=page.get_by_role('button',name='Создать вклад',exact=True)
    box=button.bounding_box()
    assert 80<box['y']<170 and box['width']<300 and box['x']>900
    button.click()
    modal=page.get_by_role('dialog',name='Новый вклад',exact=True)
    box=modal.bounding_box()
    assert abs(box['y']+box['height']/2-450)<2
    assert box['y']+box['height']<850
    page.get_by_role('button',name='Закрыть',exact=True).click()
    page.set_viewport_size({'width':390,'height':844})
    button=page.get_by_role('button',name='Создать вклад',exact=True)
    box=button.bounding_box()
    assert box['y']>750 and box['width']>=350
    button.click()
    box=page.get_by_role('dialog',name='Новый вклад',exact=True).bounding_box()
    assert abs(box['y']+box['height']-844)<2
    browser.close()
    print('PASS: top compact desktop action, centered desktop form, bottom full-width mobile action and bottom sheet')
