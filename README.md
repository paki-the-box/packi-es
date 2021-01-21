# Sample Backend for Packi based on Event Sourcing

This Example is based on https://github.com/johnbywater/es-example-taxi-demo

# Get started

## Install dependencies

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt 
```

# How to generate openapi clients (e.g. angular)

## Install openapi-generator

```
npm install @openapitools/openapi-generator-cli -g
```

(See https://openapi-generator.tech/docs/installation/)

## Generate!

```
npx @openapitools/openapi-generator-cli generate -i http://localhost:8000/openapi.json  -o src/app/backend -g typescript-angular
```
(if the server is running).