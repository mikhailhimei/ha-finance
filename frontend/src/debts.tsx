import { useEffect, useState } from 'react';
import type { Data, Hass } from './types';
import { Field, Metric, Modal } from './components';
import { Navigation } from './navigation';
import { Skeleton } from './skeleton';
import { kopecks, money, today } from './finance';
import { useDepositNavigation } from './use-deposit-navigation';

export function Debts({data,hass,loading,selectTab,openSidebar}:{data:Data;hass?:Hass;loading:boolean;selectTab:(tab:number)=>void;openSidebar:()=>void}){
 const [dialog,setDialog]=useState<'create'|'payment'>(),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const {selected,navigate,surface}=useDepositNavigation(Boolean(dialog),'haFinanceDebt');
 const debt=data.debts?.find(d=>d.id===selected);
 useEffect(()=>{setDialog(undefined);setError('')},[selected]);
 async function submit(event:React.FormEvent<HTMLFormElement>){
  event.preventDefault();const form=new FormData(event.currentTarget);setBusy(true);setError('');
  try{
   if(!hass)throw Error('Откройте панель в Home Assistant');
   const payload=dialog==='create'?{name:form.get('name'),principal:kopecks(String(form.get('principal'))),remaining:kopecks(String(form.get('remaining')))}:{debt_id:debt!.id,amount:kopecks(String(form.get('amount'))),date:today()};
   await hass.callWS({type:'ha_finance/mutate',action:dialog==='create'?'debt_create':'debt_payment',payload});setDialog(undefined);
  }catch(e){setError(e instanceof Error?e.message:String(e))}finally{setBusy(false)}
 }
 return <section ref={surface} className="debt-page">
 {debt?<header className="toolbar deposit-toolbar"><button className="icon-button" aria-label="Все долги" onClick={()=>navigate(undefined)}>←</button><div className="toolbar-title"><h1>{debt.name}</h1></div><span className="header-spacer"/></header>:<Navigation tab={3} select={selectTab} openSidebar={openSidebar}/>}
 {error&&!dialog&&<p className="error" role="alert">{error}</p>}
 {loading?<Skeleton variant="cards"/>:debt?<><section className="debt-summary"><Metric label="Текущий остаток" value={debt.remaining}/><Metric label="Изначальная сумма" value={debt.principal}/></section>{debt.payments.length>0&&<section className="debt-payments"><h2>Внесённые платежи</h2>{[...debt.payments].reverse().map(payment=><div className="expense" key={payment.id}><span>{new Date(payment.date+'T12:00:00').toLocaleDateString('ru-RU')}</span><strong>−{money(payment.amount)}</strong></div>)}</section>}<div className="expense-dock"><button className="primary" disabled={debt.remaining===0} onClick={()=>setDialog('payment')}>{debt.remaining===0?'Долг погашен':'Добавить'}</button></div></>:<>{!data.debts?.length?<section className="empty"><h2>Долгов пока нет</h2></section>:<div className="cards">{[...data.debts].reverse().map(d=><button className="card" key={d.id} onClick={()=>navigate(d.id)}><h3>{d.name}<span>↗</span></h3><Metric label="Текущий остаток" value={d.remaining}/><div className="small-metrics"><Metric label="Изначальная сумма" value={d.principal}/></div></button>)}</div>}<div className="expense-dock"><button className="primary" onClick={()=>setDialog('create')}>Создать долг</button></div></>}
 {dialog&&<Modal bottom title={dialog==='create'?'Новый долг':'Внести платёж'} close={()=>{if(!busy)setDialog(undefined)}}>{error&&<p className="error" role="alert">{error}</p>}<form onSubmit={submit}>{dialog==='create'?<><Field label="Наименование" name="name" required maxLength={150} autoFocus/><Field label="Изначальная сумма, ₽" name="principal" type="number" min="0" max="1000000000000" step="0.01" required/><Field label="Текущий остаток, ₽" name="remaining" type="number" min="0" max="1000000000000" step="0.01" required/></>:<Field label="Внесённая сумма, ₽" name="amount" type="number" min="0.01" max={debt!.remaining/100} step="0.01" required autoFocus/>}<button className="primary" disabled={busy}>{busy?'Сохранение…':'Сохранить'}</button></form></Modal>}
 </section>
}
