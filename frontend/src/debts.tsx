import { useEffect, useState } from 'react';
import type { Data, Debt, Hass } from './types';
import { Field, Metric, Modal } from './components';
import { Navigation } from './navigation';
import { Skeleton } from './skeleton';
import { HoldCard } from './hold-card';
import { ActionSheet, Pencil } from './action-sheet';
import { kopecks, money, today } from './finance';
import { useDepositNavigation } from './use-deposit-navigation';

export function Debts({data,hass,loading,selectTab,openSidebar}:{data:Data;hass?:Hass;loading:boolean;selectTab:(tab:number)=>void;openSidebar:()=>void}){
 const [dialog,setDialog]=useState<'create'|'edit'|'payment'>(),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const [editing,setEditing]=useState<Debt>(),[actions,setActions]=useState<Debt>(),[deleting,setDeleting]=useState<Debt>(),[paymentToDelete,setPaymentToDelete]=useState<Debt['payments'][number]>();
 const {selected,navigate,surface}=useDepositNavigation(Boolean(dialog||actions||deleting||paymentToDelete),'haFinanceDebt');
 const debt=data.debts?.find(d=>d.id===selected);
 useEffect(()=>{setDialog(undefined);setError('');setActions(undefined);setPaymentToDelete(undefined)},[selected]);
 async function mutate(action:string,payload:object){
  setBusy(true);setError('');try{if(!hass)throw Error('Откройте панель в Home Assistant');await hass.callWS({type:'ha_finance/mutate',action,payload});setDialog(undefined)}catch(e){setError(e instanceof Error?e.message:String(e))}finally{setBusy(false)}
 }
 function submit(event:React.FormEvent<HTMLFormElement>){
  event.preventDefault();const form=new FormData(event.currentTarget);setError('');
  try{
   if(dialog==='payment')void mutate('debt_payment',{debt_id:debt!.id,amount:kopecks(String(form.get('amount'))),date:today()});
   else void mutate(dialog==='edit'?'debt_update':'debt_create',{debt_id:editing?.id,name:form.get('name'),principal:kopecks(String(form.get('principal')))});
  }catch(e){setError(e instanceof Error?e.message:String(e))}
 }
 return <section ref={surface} className="debt-page">
 {debt?<header className="toolbar deposit-toolbar"><button className="icon-button" aria-label="Все долги" onClick={()=>navigate(undefined)}>←</button><div className="toolbar-title"><h1>{debt.name}</h1></div><button className="icon-button" aria-label="Действия с долгом" onClick={()=>setActions(debt)}><Pencil/></button></header>:<Navigation tab={3} select={selectTab} openSidebar={openSidebar}/>}
 {error&&!dialog&&<p className="error" role="alert">{error}</p>}
 {loading?<Skeleton variant="cards"/>:debt?<><section className="debt-summary"><Metric label="Остаток" value={debt.remaining}/><Metric label="Изначальная сумма" value={debt.principal}/></section>{debt.payments.length>0&&<section className="debt-payments"><h2>Внесённые платежи</h2>{[...debt.payments].reverse().map(payment=><div className="expense" key={payment.id}><span>{new Date(payment.date+'T12:00:00').toLocaleDateString('ru-RU')}</span><strong>−{money(payment.amount)}</strong><button aria-label={`Удалить платёж ${money(payment.amount)}`} onClick={()=>setPaymentToDelete(payment)}>×</button></div>)}</section>}<div className="expense-dock"><button className="primary" disabled={debt.remaining===0} onClick={()=>setDialog('payment')}>{debt.remaining===0?'Долг погашен':'Добавить'}</button></div></>:<>{!data.debts?.length?<section className="empty"><h2>Долгов пока нет</h2></section>:<div className="cards">{[...data.debts].reverse().map(d=><HoldCard className="card" key={d.id} name={d.name} open={()=>navigate(d.id)} onHold={()=>setActions(d)}><h3>{d.name}<span>↗</span></h3><Metric label="Остаток" value={d.remaining}/><div className="small-metrics"><Metric label="Изначальная сумма" value={d.principal}/></div></HoldCard>)}</div>}<div className="expense-dock"><button className="primary" onClick={()=>{setEditing(undefined);setDialog('create')}}>Создать долг</button></div></>}
 {actions&&<ActionSheet title={actions.name} close={()=>setActions(undefined)} actions={[{label:'Редактировать',run:()=>{setEditing(actions);setDialog('edit')}},{label:'Удалить',danger:true,run:()=>setDeleting(actions)},{label:'Отмена',run:()=>setActions(undefined)}]}/>}
 {deleting&&<ActionSheet title="Удалить долг?" description={`«${deleting.name}» и все внесённые платежи будут удалены.`} close={()=>setDeleting(undefined)} actions={[{label:'Удалить',danger:true,run:()=>void mutate('debt_delete',{debt_id:deleting.id})},{label:'Отмена',run:()=>setDeleting(undefined)}]}/>}
 {paymentToDelete&&debt&&<ActionSheet title="Удалить платёж?" description={`${money(paymentToDelete.amount)} вернётся в остаток долга.`} close={()=>setPaymentToDelete(undefined)} actions={[{label:'Удалить',danger:true,run:()=>void mutate('debt_payment_delete',{debt_id:debt.id,payment_id:paymentToDelete.id})},{label:'Отмена',run:()=>setPaymentToDelete(undefined)}]}/>}
 {dialog&&<Modal bottom title={dialog==='create'?'Новый долг':dialog==='edit'?'Редактировать долг':'Внести платёж'} close={()=>{if(!busy)setDialog(undefined)}}>{error&&<p className="error" role="alert">{error}</p>}<form onSubmit={submit}>{dialog!=='payment'?<><Field label="Наименование" name="name" required maxLength={150} defaultValue={dialog==='edit'?editing?.name:undefined} autoFocus/><Field label="Изначальная сумма, ₽" name="principal" type="number" min="0" max="1000000000000" step="0.01" required defaultValue={dialog==='edit'?editing!.principal/100:undefined}/></>:<Field label="Внесённая сумма, ₽" name="amount" type="number" min="0.01" max={debt!.remaining/100} step="0.01" required autoFocus/>}<button className="primary" disabled={busy}>{busy?'Сохранение…':'Сохранить'}</button></form></Modal>}
 </section>
}
