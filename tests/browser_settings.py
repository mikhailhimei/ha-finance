from playwright.sync_api import sync_playwright, expect
import json
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':390,'height':844})
    page.goto('http://127.0.0.1:8765/')
    page.evaluate('''() => {
      document.getElementById('root').remove();let rule;
      const panel=document.createElement('ha-finance-panel');
      window.calls=[];
      panel.hass={connection:{subscribeMessage:async cb=>()=>{}},callWS:async msg=>{
        if(msg.type==='ha_finance/calendar')return rule||{year:msg.year,confirmed:false,days_off:[],working_days:[]};
        if(msg.type==='ha_finance/mutate'){window.calls.push(msg);if(msg.action==='calendar_import')rule=msg.payload.calendar;if(msg.action==='calendar_reset')rule=undefined}return {deposits:[]};
      }};document.body.append(panel);
    }''')
    panel=page.locator('ha-finance-panel')
    panel.get_by_role('button',name='Открыть разделы финансов').click()
    panel.get_by_role('button',name='Настройки',exact=True).click()
    panel.get_by_role('combobox',name='Год календаря').select_option('2028')
    textarea=panel.locator('textarea.calendar-json')
    expect(textarea).to_have_value(__import__('re').compile('.*2028.*',__import__('re').S))
    textarea.fill('{broken')
    panel.get_by_role('button',name='Применить календарь').click()
    expect(panel.get_by_role('alert')).to_be_visible()
    calendar={'year':2028,'confirmed':True,'days_off':['2028-01-01'],'working_days':[]}
    panel.locator('input[type=file]').set_input_files({'name':'calendar.json','mimeType':'application/json','buffer':json.dumps(calendar).encode()})
    expect(textarea).to_have_value(json.dumps(calendar))
    panel.get_by_role('button',name='Применить календарь').click()
    expect(panel.get_by_role('status')).to_contain_text('Календарь сохранён')
    assert page.evaluate('window.calls.at(-1).payload.calendar.year')==2028
    with page.expect_download() as download:
        panel.get_by_role('button',name='Скачать JSON').click()
    assert download.value.suggested_filename=='ha-finance-calendar-2028.json'
    page.on('dialog',lambda d:d.accept())
    panel.get_by_role('button',name='Восстановить встроенный').click()
    expect(panel.get_by_role('status')).to_contain_text('Встроенный календарь восстановлен')
    browser.close();print('PASS: calendar year selection, JSON upload and validation feedback, apply, download, reset')
