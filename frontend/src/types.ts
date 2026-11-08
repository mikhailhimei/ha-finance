export type Expense = {id:string; name:string; amount:number; date:string; paid:boolean; kind?:'expense'|'income'};
export type Deposit = {id:string; name:string; principal:number; expenses:Expense[]};
export type Worker = {id:string;name:string;employment:'TK'|'fixed';income:number;advance_day?:number;salary_day?:number;fixed_day?:number};
export type Budget = {id:string;name:string;month:string;expenses:{id:string;name:string;amount:number;comment:string;month:string;payment_id:string}[]};
export type Debt = {id:string;name:string;principal:number;remaining:number;payments:{id:string;amount:number;date:string}[]};
export type Data = {deposits:Deposit[];workers?:Worker[];budgets?:Budget[];debts?:Debt[]};
export type Hass = {callWS:<T>(msg:object)=>Promise<T>; connection:{subscribeMessage:<T>(cb:(data:T)=>void,msg:object)=>Promise<()=>void>}};
