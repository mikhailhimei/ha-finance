export type Expense = {id:string; name:string; amount:number; date:string; paid:boolean};
export type Deposit = {id:string; name:string; principal:number; expenses:Expense[]};
export type Data = {deposits:Deposit[]};
export type Hass = {callWS:<T>(msg:object)=>Promise<T>; connection:{subscribeMessage:<T>(cb:(data:T)=>void,msg:object)=>Promise<()=>void>}};
