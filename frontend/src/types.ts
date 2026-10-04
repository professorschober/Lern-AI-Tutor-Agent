export type Topic = {id:string; title:string; state:string; independent:number; attempts:number; available:number}
export type Material = {id:string; name:string; topic:string|null; tables:string[]; sections:{location:string;text:string}[]}
export type Table = {name:string; allowed:boolean; columns:{name:string;type:string}[]; relationships:{column:string;target:string;target_column:string}[]}
export type Exercise = {id?:string; title:string; topic:string; prompt:string; reference_sql?:string; hints?:string[]; material_ids:string[]; tables:string[]; order_matters:boolean; aliases_matter:boolean; status?:string; version?:number}
export type Session = {id:string; exercise_id:string; hint_level:number; solution_seen:boolean}
export type Result = {execution:string; verdict:string; columns:string[]; rows:unknown[][]; feedback_code:string; message?:string}
export type Attempt = {id:string; sql:string; result:Result; topic:string; created:string; version:number; supported:boolean}
export type Chat = {id?:string; message:string; response:string; fallback?:boolean}
