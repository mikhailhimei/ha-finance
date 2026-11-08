import type { Deposit } from './types';
import { total } from './finance';
import { Metric } from './components';
import { HoldCard } from './hold-card';

export function DepositCard({deposit,open,edit,remove}:{deposit:Deposit;open:()=>void;edit:()=>void;remove:()=>void}){
 const x=total(deposit);
 return <div className="deposit-card-wrap"><HoldCard name={deposit.name} className="card" open={open} edit={edit} remove={remove}>
  <h3>{deposit.name}<span>↗</span></h3><Metric label="Свободные деньги" value={x.available}/><div className="small-metrics"><Metric label="Общая сумма" value={x.principal}/><Metric label="Оплачено" value={x.actual}/><Metric label="Ожидается" value={x.expected}/></div>
 </HoldCard></div>
}
