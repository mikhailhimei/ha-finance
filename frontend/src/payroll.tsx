import { useEffect, useState } from 'react';
import type { Hass, Worker } from './types';
import { Field, Metric, Modal } from './components';
import { kopecks, money, today } from './finance';
import { Pencil } from './action-sheet';
import { Navigation } from './navigation';

type Estimate={workdays:number;first_workdays:number;second_workdays:number;salary_workdays:number;salary_first_workdays:number;advance_period:string;salary_period:string;advance:number;salary:number;advance_date:string;salary_date:string};
const formatDate=(date:string)=>new Date(date+'T12:00:00').toLocaleDateString('ru-RU');
function WorkerPreview({worker,hass}:{worker:Worker;hass?:Hass}){
 const [estimate,setEstimate]=useState<Estimate>(),[error,setError]=useState('');
 const month=today().slice(0,7);
 useEffect(()=>{
  let active=true;setEstimate(undefined);setError('');
  if(!hass)return;
  const [year,m]=month.split('-').map(Number);
  hass.callWS<Estimate>({type:'ha_finance/payroll',worker_id:worker.id,year,month:m}).then(result=>{if(active)setEstimate(result)}).catch(e=>{if(active)setError(String(e.message||e))});
  return ()=>{active=false};
 },[worker,hass,month]);
 return <>{error?<span className="error">{error}</span>:!estimate?<span className="muted">Расчёт выплат…</span>:<div className="worker-preview-payments"><div><span>Зарплата · {formatDate(estimate.salary_date)}</span><strong>{money(estimate.salary)}</strong></div><div><span>Аванс · {formatDate(estimate.advance_date)}</span><strong>{money(estimate.advance)}</strong></div></div>}</>;
}
export function Payroll({workers,hass,selectTab,openSidebar}:{workers:Worker[];hass?:Hass;selectTab:(tab:number)=>void;openSidebar:()=>void}){
 const [open,setOpen]=useState(false),[editing,setEditing]=useState<Worker>(),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const [selected,setSelected]=useState<string>(),[month,setMonth]=useState(today().slice(0,7)),[estimate,setEstimate]=useState<Estimate>(),[calculationError,setCalculationError]=useState('');
 const worker=workers.find(w=>w.id===selected);
 useEffect(()=>{
  setEstimate(undefined);setCalculationError('');let active=true;
  if(!worker||!hass)return;
  const [year,m]=month.split('-').map(Number);
  hass.callWS<Estimate>({type:'ha_finance/payroll',worker_id:worker.id,year,month:m}).then(result=>{if(active)setEstimate(result)}).catch(e=>{if(active)setCalculationError(String(e.message||e))});
  return ()=>{active=false};
 },[worker,hass,month]);
 const start=(worker?:Worker)=>{setEditing(worker);setError('');setOpen(true)};
 async function submit(event:React.FormEvent<HTMLFormElement>){
  event.preventDefault();const form=new FormData(event.currentTarget);setBusy(true);setError('');
  try{
   if(!hass)throw Error('Для сохранения откройте панель в Home Assistant.');
   await hass.callWS({type:'ha_finance/mutate',action:'worker_save',payload:{worker_id:editing?.id,name:form.get('name'),employment:form.get('employment'),income:kopecks(String(form.get('income'))),advance_day:Number(form.get('advance_day')),salary_day:Number(form.get('salary_day'))}});
   setOpen(false);
  }catch(e){setError(e instanceof Error?e.message:String(e))}finally{setBusy(false)}
 }
 return <section className="payroll">
  {!worker&&<Navigation tab={2} select={selectTab} openSidebar={openSidebar}/>}
  {worker?<><header className="toolbar deposit-toolbar"><button className="icon-button" aria-label="Все работники" onClick={()=>setSelected(undefined)}>←</button><div className="toolbar-title"><h1>{worker.name}</h1></div><button className="icon-button" aria-label={`Изменить работника ${worker.name}`} onClick={()=>start(worker)}><Pencil/></button></header><Field label="Месяц выплат" type="month" min="2025-01" max="2027-12" required value={month} onChange={e=>setMonth(e.target.value)}/>
  {calculationError?<p className="error" role="alert">{calculationError}</p>:!estimate?<p className="muted">Расчёт…</p>:<><div className="salary-payments"><article className="worker-card"><Metric label="Зарплата" value={estimate.salary}/><p className="payment-date">{formatDate(estimate.salary_date)}</p><span className="muted">За 16–конец месяца · {estimate.salary_period}<br/>{estimate.second_workdays} рабочих дней</span></article><article className="worker-card"><Metric label="Аванс" value={estimate.advance}/><p className="payment-date">{formatDate(estimate.advance_date)}</p><span className="muted">За 1–15 число · {estimate.advance_period}<br/>{estimate.first_workdays} рабочих дней</span></article></div><p className="muted">{money(worker.income)} ÷ {estimate.workdays} раб. дн. × {estimate.first_workdays} раб. дн. = {money(estimate.advance)}</p><p className="muted salary-note">Расчёт за полностью отработанный месяц по федеральной пятидневке РФ. Без автоматического вычета НДФЛ, отпусков и больничных. Зарплата — за вторую половину предыдущего месяца; аванс — за первую половину выбранного. Сумма выплат за календарный месяц может отличаться от месячного дохода. Выплаты в нерабочие дни перенесены на предыдущий рабочий день.</p></>}
  </>:workers.length===0?<div className="empty"><span className="empty-icon">₽</span><h2>Работники пока не указаны</h2><p>Добавьте работника, его доход и дни выплат.</p></div>:<div className="cards">{workers.map(worker=><article className="worker-card" key={worker.id}><header><h2><button className="worker-open" onClick={()=>setSelected(worker.id)}>{worker.name} <span aria-hidden="true">↗</span></button></h2><button className="icon-button" aria-label={`Изменить работника ${worker.name}`} onClick={()=>start(worker)}><Pencil/></button></header><button className="worker-body" aria-label={`Открыть работника ${worker.name}`} onClick={()=>setSelected(worker.id)}><span className="employment-badge">ТК</span><Metric label="Доход за месяц" value={worker.income}/><WorkerPreview worker={worker} hass={hass}/></button></article>)}</div>}
  {!worker&&<div className="expense-dock"><button className="primary" onClick={()=>start()}><span aria-hidden="true">＋</span> Указать работника</button></div>}
  {open&&<Modal bottom title={editing?'Изменить работника':'Указать работника'} close={()=>{if(!busy)setOpen(false)}}>{error&&<p className="error" role="alert">{error}</p>}<form onSubmit={submit}>
   <Field label="Наименование" name="name" required maxLength={150} defaultValue={editing?.name} autoFocus/>
   <label className="field">Тип оформления<select name="employment" defaultValue="TK"><option value="TK">ТК</option></select></label>
   <Field label="Доход, ₽" name="income" type="number" min="0" max="1000000000000" step="0.01" required defaultValue={editing?editing.income/100:undefined}/>
   <div className="payment-days"><Field label="Число зарплаты" name="salary_day" type="number" min="1" max="31" step="1" required defaultValue={editing?.salary_day}/><Field label="Число аванса" name="advance_day" type="number" min="1" max="31" step="1" required defaultValue={editing?.advance_day}/></div>
   <button className="primary" disabled={busy}>{busy?'Сохранение…':'Сохранить'}</button>
  </form></Modal>}
 </section>
}
