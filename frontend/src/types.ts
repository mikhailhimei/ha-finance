export type Expense = {id:string; name:string; amount:number; date:string; paid:boolean; kind?:'expense'|'income'};
export type Deposit = {id:string; name:string; principal:number; expenses:Expense[]};
export type Worker = {id:string;name:string;employment:'TK'|'fixed';income:number;advance_day?:number;salary_day?:number;fixed_day?:number};
export type Data = {deposits:Deposit[];workers?:Worker[]};
export type Hass = {callWS:<T>(msg:object)=>Promise<T>; connection:{subscribeMessage:<T>(cb:(data:T)=>void,msg:object)=>Promise<()=>void>}};
