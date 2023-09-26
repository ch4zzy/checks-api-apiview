# Checks-api using APIView only

## Endpoints

```
GET, POST.

~/api/check/ - get list or create check.
~/api/printer/ - get list or create printer.
```

```
GET, PUT, DELETE.

~/api/check/<int:pk>/ - get, update or delete check.
~/api/printer/<int:pk>/ - get, update or delete printer.
```

```
POST.

~/api/check/create/ - create check based on printers.
```

```json
POST DATA.

{
  "point_id": 1,
  "order": {
    "order_id": 2,
    "item": "Milk",
    "quantity": 2,
    "price": 10.99
  }
}
```

```
GET, PUT.

~/api/check/<int:pk>/update/ - print check and update status.
```
