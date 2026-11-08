import { useEffect, useRef, useState } from 'react';
import type { Deposit } from './types';
import { total } from './finance';
import { Metric } from './components';

export function DepositCard({deposit,open,remove}:{deposit:Deposit;open:()=>void;remove:()=>void}){
 const [actions,setActions]=useState(false);
 const timer=useRef<ReturnType<typeof setTimeout>|undefined>(undefined);
 const origin=useRef<{x:number;y:number}|undefined>(undefined);
 const held=useRef(false);
 const cancel=()=>{clearTimeout(timer.current);timer.current=undefined};
 useEffect(()=>()=>clearTimeout(timer.current),[]);
 const x=total(deposit);
 return <div className="deposit-card-wrap">
  <button className="card" aria-label={deposit.name} onPointerDown={event=>{
   if(!event.isPrimary||event.button!==0)return;
   cancel();held.current=false;origin.current={x:event.clientX,y:event.clientY};
   timer.current=setTimeout(()=>{held.current=true;setActions(true)},600);
  }} onPointerMove={event=>{if(origin.current&&Math.hypot(event.clientX-origin.current.x,event.clientY-origin.current.y)>10)cancel()}}
  onPointerUp={cancel} onPointerCancel={cancel} onPointerLeave={cancel}
  onContextMenu={event=>{event.preventDefault();cancel();held.current=true;setActions(true)}}
  onKeyDown={event=>{if(event.key==='Escape')setActions(false);if(event.key==='F10'&&event.shiftKey){event.preventDefault();setActions(true)}}}
  onClick={()=>{if(held.current){held.current=false;return}if(actions){setActions(false);return}open()}}>
   <h3>{deposit.name}<span>↗</span></h3><Metric label="Свободные деньги" value={x.available}/><div className="small-metrics"><Metric label="Общая сумма" value={x.principal}/><Metric label="Оплачено" value={x.actual}/><Metric label="Ожидается" value={x.expected}/></div>
  </button>
  {actions&&<div className="card-actions"><button className="destructive" onClick={remove}>Удалить</button><button onClick={()=>setActions(false)}>Отмена</button></div>}
 </div>
}
