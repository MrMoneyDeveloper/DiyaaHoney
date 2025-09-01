dbdiagram.io syntax

Table users {
  id int [pk, increment]
  username varchar [unique]
  password varchar
  role varchar
}

Table connections {
  id int [pk, increment]
  ip varchar
  port int
  ts timestamp
  user_id int [ref: > users.id]
}

Table alerts {
  id int [pk, increment]
  ip varchar
  message varchar
  ts timestamp
}
