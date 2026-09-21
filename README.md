# Employee Management API

A minimal FastAPI assessment project deployed as:

```text
Postman → Azure API Management → Azure Container Apps → FastAPI (in-memory data)
```

Employee data is intentionally stored in memory. It resets when the application restarts or a new Container Apps revision is deployed.

## Project structure

```text
employee_management_api/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── schemas.py
│   └── routers/employees.py
├── postman/
│   ├── Employee-Management-API.postman_collection.json
│   └── Employee-Management-API.postman_environment.json
├── .env.example
├── Dockerfile
├── requirements.txt
└── README.md
```

The Postman files are retained because the assignment explicitly requires a collection and demonstrations of successful, unauthorized, missing-header, rate-limited, and transformed requests.

## API operations

| Method | Path | Purpose |
|---|---|---|
| POST | `/employees` | Create an employee |
| GET | `/employees` | List employees |
| GET | `/employees/{id}` | Get one employee |
| DELETE | `/employees/{id}` | Delete an employee |
| GET | `/health` | Check deployment/version |

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000/docs
http://localhost:8000/health
```

## Docker

```powershell
docker build -t employee-api:v1 .
docker run --name employee-api -p 8000:8000 -e APP_ENVIRONMENT=local-container -e APP_VERSION=1.0.0 employee-api:v1
```

Test `http://localhost:8000/health`, then stop/remove the container:

```powershell
docker stop employee-api
docker rm employee-api
```

## Push to your Azure Container Registry

Your registry is `acremployeeapi12345.azurecr.io`:

```powershell
docker login acremployeeapi12345.azurecr.io
docker tag employee-api:v1 acremployeeapi12345.azurecr.io/employee-api:v1
docker push acremployeeapi12345.azurecr.io/employee-api:v1
```

The spelling must be exact: `acremployeeapi12345`, not `acreemployeeapi12345`.

## Container Apps configuration

Deploy `acremployeeapi12345.azurecr.io/employee-api:v1` with:

```text
Ingress: Enabled
Ingress type: External
Target port: 8000
Minimum replicas: 1
Maximum replicas: 1
```

Environment variables:

```text
APP_ENVIRONMENT=azure
APP_VERSION=1.0.0
LOG_LEVEL=INFO
```

Verify:

```text
https://<CONTAINER-APP-HOST>/health
https://<CONTAINER-APP-HOST>/openapi.json
```

## Import the API into APIM

In `employee-api-apim`:

1. Select **APIs → OpenAPI → Full**.
2. Set **OpenAPI specification** to `https://<CONTAINER-APP-HOST>/openapi.json`.
3. Set display name to `Employee Management API`.
4. Set name to `employee-api`.
5. Set API URL suffix to `employees-api`.
6. Select HTTPS and leave Products blank.
7. Create the API.
8. Open its **Settings** and confirm the Web service URL is `https://<CONTAINER-APP-HOST>`.
9. Enable **Subscription required** and save.

The APIM base URL becomes:

```text
https://employee-api-apim.azure-api.net/employees-api
```

## Create APIM products

Create these under **APIM → Products → Add**:

### HR

```text
Display name: HR
ID: hr
State: Published
Requires subscription: Yes
Requires approval: No
API: Employee Management API
```

### Manager

```text
Display name: Manager
ID: manager
State: Published
Requires subscription: Yes
Requires approval: No
API: Employee Management API
```

Ensure the API is associated only with HR and Manager—not Starter or Unlimited.

## HR product policy

Open **Products → HR → Policies**, use the code editor, replace the policy with this XML, and save:

```xml
<policies>
  <inbound>
    <base />
    <choose>
      <when condition="@(!context.Request.Headers.ContainsKey(&quot;X-Department&quot;))">
        <return-response>
          <set-status code="400" reason="Bad Request" />
          <set-header name="Content-Type" exists-action="override"><value>application/json</value></set-header>
          <set-body>{"error":"missing_department_header","message":"X-Department header is required."}</set-body>
        </return-response>
      </when>
      <when condition="@(!context.Request.Headers.GetValueOrDefault(&quot;X-Department&quot;, &quot;&quot;).Equals(&quot;HR&quot;, StringComparison.OrdinalIgnoreCase))">
        <return-response>
          <set-status code="403" reason="Forbidden" />
          <set-header name="Content-Type" exists-action="override"><value>application/json</value></set-header>
          <set-body>{"error":"invalid_department_header","message":"This subscription requires X-Department: HR."}</set-body>
        </return-response>
      </when>
    </choose>
  </inbound>
  <backend><base /></backend>
  <outbound><base /></outbound>
  <on-error><base /></on-error>
</policies>
```

## Manager product policy

Open **Products → Manager → Policies**, replace the policy with this XML, and save:

```xml
<policies>
  <inbound>
    <base />
    <choose>
      <when condition="@(!context.Request.Headers.ContainsKey(&quot;X-Department&quot;))">
        <return-response>
          <set-status code="400" reason="Bad Request" />
          <set-header name="Content-Type" exists-action="override"><value>application/json</value></set-header>
          <set-body>{"error":"missing_department_header","message":"X-Department header is required."}</set-body>
        </return-response>
      </when>
      <when condition="@(!context.Request.Headers.GetValueOrDefault(&quot;X-Department&quot;, &quot;&quot;).Equals(&quot;Manager&quot;, StringComparison.OrdinalIgnoreCase))">
        <return-response>
          <set-status code="403" reason="Forbidden" />
          <set-header name="Content-Type" exists-action="override"><value>application/json</value></set-header>
          <set-body>{"error":"invalid_department_header","message":"This subscription requires X-Department: Manager."}</set-body>
        </return-response>
      </when>
      <when condition="@(context.Request.Method != &quot;GET&quot;)">
        <return-response>
          <set-status code="403" reason="Forbidden" />
          <set-header name="Content-Type" exists-action="override"><value>application/json</value></set-header>
          <set-body>{"error":"operation_not_allowed","message":"Managers may perform GET operations only."}</set-body>
        </return-response>
      </when>
    </choose>
  </inbound>
  <backend><base /></backend>
  <outbound><base /></outbound>
  <on-error><base /></on-error>
</policies>
```

## API rate-limit and response policy

Open **APIs → Employee Management API → All operations → Policies**, replace the policy with this XML, and save:

```xml
<policies>
  <inbound>
    <base />
    <rate-limit-by-key calls="20"
                       renewal-period="60"
                       counter-key="@(context.Subscription.Id)"
                       retry-after-header-name="Retry-After"
                       remaining-calls-header-name="X-RateLimit-Remaining" />
  </inbound>
  <backend><base /></backend>
  <outbound>
    <base />
    <choose>
      <when condition="@(context.Response.StatusCode != 204 &amp;&amp; context.Response.Headers.GetValueOrDefault(&quot;Content-Type&quot;, &quot;&quot;).Contains(&quot;application/json&quot;))">
        <set-body>@{
          var body = context.Response.Body.As&lt;Newtonsoft.Json.Linq.JToken&gt;(preserveContent: true);
          var item = body as Newtonsoft.Json.Linq.JObject;
          if (item != null) {
            var property = item.Property("internal_notes");
            if (property != null) property.Remove();
          }
          var items = body as Newtonsoft.Json.Linq.JArray;
          if (items != null) {
            foreach (var token in items) {
              var employee = token as Newtonsoft.Json.Linq.JObject;
              if (employee != null) {
                var property = employee.Property("internal_notes");
                if (property != null) property.Remove();
              }
            }
          }
          return body.ToString(Newtonsoft.Json.Formatting.None);
        }</set-body>
      </when>
    </choose>
  </outbound>
  <on-error><base /></on-error>
</policies>
```

## Create subscriptions

Under **APIM → Subscriptions → Add** create:

```text
Name: HR Postman Demo
Scope: Product → HR
```

```text
Name: Manager Postman Demo
Scope: Product → Manager
```

Copy each primary key without exposing it in screenshots.

## Postman testing

Import the two files from `postman/`, select the imported environment, and set:

```text
baseUrl=https://employee-api-apim.azure-api.net/employees-api
hrSubscriptionKey=<HR primary key>
managerSubscriptionKey=<Manager primary key>
```

Run the collection folders in order. Required evidence:

| Test | Expected result |
|---|---:|
| HR POST with `X-Department: HR` | 201; `internal_notes` removed |
| HR GET/DELETE | 200/204 |
| Manager GET with `X-Department: Manager` | 200 |
| Manager POST or DELETE | 403 |
| Missing subscription key | 401 |
| Missing department header | 400 |
| Invalid department header | 403 |
| More than 20 rapid requests | 429 with `Retry-After` |

For throttling evidence, run the rate-limit folder in Collection Runner for 25 iterations.

## Version 2 update

After capturing v1 evidence, make a visible Python change. Add this field to `HealthResponse` in `app/schemas.py`:

```python
release_message: str
```

Then add this argument to `HealthResponse(...)` in `app/main.py`:

```python
release_message="Employee API v2 deployment verified",
```

This repository now includes that v2 change. The `/health` response includes both
`"version": "1.1.0"` and `"release_message": "Employee API v2 deployment verified"`.

Build and push a new immutable tag:

```powershell
docker build -t employee-api:v2 .
docker tag employee-api:v2 acremployeeapi12345.azurecr.io/employee-api:v2
docker push acremployeeapi12345.azurecr.io/employee-api:v2
```

Update the Container App image to `acremployeeapi12345.azurecr.io/employee-api:v2`, set `APP_VERSION` to `1.1.0`, deploy the new revision, and verify `/health`.
