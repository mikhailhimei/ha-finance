import { useEffect, useState } from 'react';
import type { Hass, Worker } from './types';
import { Field, Metric, Modal } from './components';
import { kopecks, money, today } from './finance';
import { HoldCard } from './hold-card';
import { ActionSheet, Pencil } from './action-sheet';
import { useDepositNavigation } from './use-deposit-navigation';
import { Navigation } from './navigation';

type Estimate={kind?:'fixed';payment?:number;payment_date?:string;workdays:number;first_workdays:number;second_workdays:number;salary_workdays:number;salary_first_workdays:number;advance_period:string;salary_period:string;advance:number;salary:number;advance_date:string;salary_date:string};
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
 return <>{error?<span className="error">{error}</span>:!estimate?<span className="muted">Расчёт выплат…</span>:estimate.kind==='fixed'?<div className="worker-preview-payments"><div><span>Доход · {formatDate(estimate.payment_date!)}</span><strong>{money(estimate.payment!)}</strong></div></div>:<div className="worker-preview-payments"><div><span>Зарплата · {formatDate(estimate.salary_date)}</span><strong>{money(estimate.salary)}</strong></div><div><span>Аванс · {formatDate(estimate.advance_date)}</span><strong>{money(estimate.advance)}</strong></div></div>}</>;
}
export function Payroll({workers,hass,selectTab,openSidebar}:{workers:Worker[];hass?:Hass;selectTab:(tab:number)=>void;openSidebar:()=>void}){
 const [open,setOpen]=useState(false),[editing,setEditing]=useState<Worker>(),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const [incomeType,setIncomeType]=useState<'TK'|'fixed'>('TK');
 const [month,setMonth]=useState(today().slice(0,7)),[estimate,setEstimate]=useState<Estimate>(),[calculationError,setCalculationError]=useState('');
 const [deleting,setDeleting]=useState<Worker>();
 const {selected,navigate:setSelected,surface}=useDepositNavigation(Boolean(open||deleting),'haFinanceWorker');
 useEffect(()=>{setOpen(false)},[selected]);
 const worker=workers.find(w=>w.id===selected);
 useEffect(()=>{
  setEstimate(undefined);setCalculationError('');let active=true;
  if(!worker||!hass)return;
  const [year,m]=month.split('-').map(Number);
  hass.callWS<Estimate>({type:'ha_finance/payroll',worker_id:worker.id,year,month:m}).then(result=>{if(active)setEstimate(result)}).catch(e=>{if(active)setCalculationError(String(e.message||e))});
  return ()=>{active=false};
 },[worker,hass,month]);
 const start=(worker?:Worker)=>{setEditing(worker);setIncomeType(worker?.employment||'TK');setError('');setOpen(true)};
 async function submit(event:React.FormEvent<HTMLFormElement>){
  event.preventDefault();const form=new FormData(event.currentTarget);setBusy(true);setError('');
  try{
   if(!hass)throw Error('Для сохранения откройте панель в Home Assistant.');
   await hass.callWS({type:'ha_finance/mutate',action:'worker_save',payload:{worker_id:editing?.id,name:form.get('name'),employment:form.get('employment'),income:kopecks(String(form.get('income'))),advance_day:Number(form.get('advance_day')),salary_day:Number(form.get('salary_day')),fixed_day:Number(form.get('fixed_day'))}});
   setOpen(false);
  }catch(e){setError(e instanceof Error?e.message:String(e))}finally{setBusy(false)}
 }
 return <section ref={surface} className="payroll">
  {!worker&&<Navigation tab={2} select={selectTab} openSidebar={openSidebar}/>}
  {worker?<><header className="toolbar deposit-toolbar"><button className="icon-button" aria-label="Все работники" onClick={()=>setSelected(undefined)}>←</button><div className="toolbar-title"><h1>{worker.name}</h1></div><button className="icon-button" aria-label={`Изменить работника ${worker.name}`} onClick={()=>start(worker)}><Pencil/></button></header><Field label="Месяц выплат" type="month" min="2025-01" max="2027-12" required value={month} onChange={e=>setMonth(e.target.value)}/>
  {calculationError?<p className="error" role="alert">{calculationError}</p>:!estimate?<p className="muted">Расчёт…</p>:estimate.kind==='fixed'?<article className="worker-card fixed-payment"><Metric label="Фиксированный доход" value={estimate.payment!}/><p className="payment-date">{formatDate(estimate.payment_date!)}</p><span className="muted">В нерабочий день выплата переносится на предыдущий рабочий.</span></article>:<><div className="salary-payments"><article className="worker-card"><Metric label="Зарплата" value={estimate.salary}/><p className="payment-date">{formatDate(estimate.salary_date)}</p><span className="muted">За 16–конец месяца · {estimate.salary_period}<br/>{estimate.second_workdays} рабочих дней</span></article><article className="worker-card"><Metric label="Аванс" value={estimate.advance}/><p className="payment-date">{formatDate(estimate.advance_date)}</p><span className="muted">За 1–15 число · {estimate.advance_period}<br/>{estimate.first_workdays} рабочих дней</span></article></div><p className="muted">{money(worker.income)} ÷ {estimate.workdays} раб. дн. × {estimate.first_workdays} раб. дн. = {money(estimate.advance)}</p><p className="muted salary-note">Расчёт за полностью отработанный месяц по федеральной пятидневке РФ. Без автоматического вычета НДФЛ, отпусков и больничных. Зарплата — за вторую половину предыдущего месяца; аванс — за первую половину выбранного. Сумма выплат за календарный месяц может отличаться от месячного дохода. Выплаты в нерабочие дни перенесены на предыдущий рабочий день.</p></>}
  </>:workers.length===0?<div className="empty"><span className="empty-icon">₽</span><h2>Работники пока не указаны</h2><p>Добавьте работника, его доход и дни выплат.</p></div>:<div className="cards">{workers.map(worker=><HoldCard key={worker.id} name={worker.name} className="worker-card" open={()=>setSelected(worker.id)} edit={()=>start(worker)} remove={()=>setDeleting(worker)}><header><h2>{worker.name}</h2><span aria-hidden="true">↗</span></header><span className="employment-badge">{worker.employment==='fixed'?'Фиксированный доход':'Зарплата офф'}</span><Metric label="Доход за месяц" value={worker.income}/><WorkerPreview worker={worker} hass={hass}/></HoldCard>)}</div>}
  {!worker&&<div className="expense-dock"><button className="primary" onClick={()=>start()}><span aria-hidden="true">＋</span> Указать работника</button></div>}
  {deleting&&<ActionSheet title="Удалить работника?" description={`«${deleting.name}» будет удалён.`} close={()=>setDeleting(undefined)} actions={[
   {label:'Удалить',danger:true,run:()=>{void (async()=>{try{if(!hass)throw Error('Откройте панель в Home Assistant');await hass.callWS({type:'ha_finance/mutate',action:'worker_delete',payload:{worker_id:deleting.id}})}catch(e){setError(e instanceof Error?e.message:String(e))}})()}},
   {label:'Отмена',run:()=>setDeleting(undefined)},
  ]}/>}
  {error&&!open&&<p className="error" role="alert">{error}</p>}
  {open&&<Modal bottom title={editing?'Изменить работника':'Указать работника'} close={()=>{if(!busy)setOpen(false)}}>{error&&<p className="error" role="alert">{error}</p>}<form onSubmit={submit}>
   <Field label="Наименование" name="name" required maxLength={150} defaultValue={editing?.name} autoFocus/>
   <label className="field">Тип дохода<select name="employment" value={incomeType} onChange={e=>setIncomeType(e.target.value as 'TK'|'fixed')}><option value="TK">Зарплата офф</option><option value="fixed">Фиксированный доход</option></select></label>
   <Field label="Доход, ₽" name="income" type="number" min="0" max="1000000000000" step="0.01" required defaultValue={editing?editing.income/100:undefined}/>
   {incomeType==='TK'?<div className="payment-days"><Field label="День зарплаты" name="salary_day" type="number" min="1" max="31" step="1" required defaultValue={editing?.salary_day}/><Field label="День аванса" name="advance_day" type="number" min="1" max="31" step="1" required defaultValue={editing?.advance_day}/></div>:<Field label="Дата дохода · число месяца" name="fixed_day" type="number" min="1" max="31" step="1" required defaultValue={editing?.fixed_day}/> }
   <button className="primary" disabled={busy}>{busy?'Сохранение…':'Сохранить'}</button>
  </form></Modal>}
 </section>
}
