import { useEffect, useState } from 'react';
import type { Hass } from './types';
import { Navigation } from './navigation';
import { Skeleton } from './skeleton';

type Calendar={year:number;confirmed:boolean;days_off:string[];working_days:string[]};
export function Settings({hass,selectTab,openSidebar}:{hass?:Hass;selectTab:(tab:number)=>void;openSidebar:()=>void}){
 const [year,setYear]=useState(new Date().getFullYear()),[json,setJson]=useState(''),[busy,setBusy]=useState(false),[loading,setLoading]=useState(false),[error,setError]=useState(''),[message,setMessage]=useState('');
 useEffect(()=>{let active=true;setError('');setMessage('');setJson('');if(!hass)return;setLoading(true);hass.callWS<Calendar>({type:'ha_finance/calendar',year}).then(c=>{if(active)setJson(JSON.stringify(c,null,2))}).catch(e=>{if(active)setError(String(e.message||e))}).finally(()=>{if(active)setLoading(false)});return ()=>{active=false}},[hass,year]);
 async function apply(reset=false){setBusy(true);setError('');setMessage('');try{
  if(!hass)throw Error('Откройте панель в Home Assistant');
  const calendar:Calendar=reset?{year,confirmed:false,days_off:[],working_days:[]}:JSON.parse(json);
  if(!reset&&calendar.year!==year)throw Error('Год в JSON должен совпадать с выбранным годом.');
  await hass.callWS({type:'ha_finance/mutate',action:reset?'calendar_reset':'calendar_import',payload:reset?{year}:{calendar}});
  const updated=await hass.callWS<Calendar>({type:'ha_finance/calendar',year});setJson(JSON.stringify(updated,null,2));
  setMessage(reset?'Встроенный календарь восстановлен.':'Календарь сохранён. Расчёты зарплаты и бюджета обновлены.');
 }catch(e){setError(e instanceof Error?e.message:String(e))}finally{setBusy(false)}}
 function download(){try{const content=JSON.stringify(JSON.parse(json),null,2);const url=URL.createObjectURL(new Blob([content],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download=`ha-finance-calendar-${year}.json`;link.click();URL.revokeObjectURL(url)}catch{setError('Некорректный JSON')}}
 return <section className="settings-page"><Navigation tab={4} select={selectTab} openSidebar={openSidebar}/><section className="calendar-settings"><h2>Производственный календарь РФ</h2><p className="muted">Загрузите полный календарь года. Субботы и воскресенья считаются выходными автоматически. В days_off указываются праздники и дополнительные выходные, в working_days — рабочие выходные. Перенос указывается двумя датами: выходной и рабочей.</p><label className="field">Год календаря<select value={year} disabled={busy} onChange={e=>setYear(Number(e.target.value))}>{Array.from({length:77},(_,i)=>2024+i).map(y=><option value={y} key={y}>{y}</option>)}</select></label>
 {error&&<p className="error" role="alert">{error}</p>}{message&&<p className="notice" role="status">{message}</p>}
 {loading?<Skeleton variant="periods" count={2}/>:<><div className="calendar-buttons"><label className="file-button">Загрузить JSON<input type="file" accept=".json,application/json" disabled={busy} onChange={async event=>{const file=event.target.files?.[0];if(!file)return;setError('');setMessage('');try{if(file.size>128*1024)throw Error('Файл должен быть не больше 128 КБ');setJson(await file.text())}catch(e){setError(String(e))}event.target.value=''}}/></label><button disabled={!json||busy} onClick={download}>Скачать JSON</button></div><label className="field">Календарь JSON<textarea className="calendar-json" rows={16} value={json} disabled={busy} onChange={e=>{setJson(e.target.value);setMessage('')}} spellCheck={false}/></label><p className="muted">confirmed: true — вы проверили календарь по утверждённым переносам. false — предварительный. Импорт полностью заменяет календарь выбранного года.</p><div className="calendar-buttons"><button className="primary" disabled={busy||!json} onClick={()=>void apply()}>{busy?'Сохранение…':'Применить календарь'}</button><button disabled={busy} onClick={()=>{if(confirm('Восстановить встроенный календарь этого года?'))void apply(true)}}>Восстановить встроенный</button></div></>}
 </section></section>
}
