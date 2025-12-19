# WordLift GraphQL Query Examples

This document contains common GraphQL queries for working with the WordLift Knowledge Graph.

## Product Queries

### Get All Products
```graphql
query {
  products(page: 0, rows: 100) {
    iri
    name: string(name: "schema:name")
    gtin: string(name: "schema:gtin14")
    sku: string(name: "schema:sku")
    brand: resource(name: "schema:brand") {
      name: string(name: "schema:name")
    }
    price: resource(name: "schema:offers") {
      price: string(name: "schema:price")
      currency: string(name: "schema:priceCurrency")
    }
    image: string(name: "schema:image")
  }
}
```

### Get Products by GTIN List
```graphql
query {
  products(
    query: {
      gtin14Constraint: { in: ["00012345678901", "00098765432109"] }
    }
    rows: 100
  ) {
    iri
    name: string(name: "schema:name")
    gtin: string(name: "schema:gtin14")
  }
}
```

### Get Product by URL
```graphql
query($url: String!) {
  entity(url: $url) {
    iri
    name: string(name: "schema:name")
    gtin: string(name: "schema:gtin14")
    description: string(name: "schema:description")
    price: resource(name: "schema:offers") {
      price: string(name: "schema:price")
      currency: string(name: "schema:priceCurrency")
      availability: string(name: "schema:availability")
    }
  }
}
```

### Get All Product GTINs (for diff checking)
```graphql
query {
  products(rows: 10000) {
    gtin: string(name: "schema:gtin14")
  }
}
```

### Get Products Modified After Date
```graphql
query {
  products(
    query: {
      dateModifiedConstraint: {
        gt: "2024-01-01T00:00:00Z"
      }
    }
    rows: 1000
  ) {
    iri
    name: string(name: "schema:name")
    gtin: string(name: "schema:gtin14")
    dateModified: string(name: "schema:dateModified")
  }
}
```

## Entity Type Queries

### Get Entities by Type
```graphql
query {
  entities(
    query: {
      typeConstraint: { in: ["http://schema.org/Product"] }
    }
    page: 0
    rows: 100
  ) {
    iri
    types: refs(name: "rdf:type")
    name: string(name: "schema:name")
  }
}
```

### Get Organizations
```graphql
query {
  entities(
    query: {
      typeConstraint: { in: ["http://schema.org/Organization"] }
    }
    rows: 100
  ) {
    iri
    name: string(name: "schema:name")
    url: string(name: "schema:url")
    logo: string(name: "schema:logo")
  }
}
```

## Filtering and Sorting

### Products by Brand
```graphql
query {
  products(
    query: {
      brandConstraint: { in: ["Brand A", "Brand B"] }
    }
    rows: 100
  ) {
    iri
    name: string(name: "schema:name")
    brand: string(name: "schema:brand")
  }
}
```

### Products by Price Range
```graphql
query {
  products(
    query: {
      priceConstraint: {
        between: { lower: "10.00", upper: "100.00" }
      }
    }
    rows: 100
  ) {
    iri
    name: string(name: "schema:name")
    price: resource(name: "schema:offers") {
      price: string(name: "schema:price")
    }
  }
}
```

### Sort Products by Name
```graphql
query {
  products(
    page: 0
    rows: 100
    orderBy: [name_ASC]
  ) {
    iri
    name: string(name: "schema:name")
  }
}
```

## Aggregation Queries

### Count Products by Brand
```graphql
query {
  products {
    brandAggregation: aggregateInt(
      name: "schema:brand"
      operation: COUNT
    ) {
      key
      count
    }
  }
}
```

## URL Filtering

### Get Entities by URL Pattern
```graphql
query {
  entities(
    query: {
      urlConstraint: { regex: { pattern: "^/products/" } }
    }
    rows: 100
  ) {
    iri
    url: string(name: "schema:url")
    name: string(name: "schema:name")
  }
}
```

## Checking Existence

### Check if Entity Exists
```graphql
query($url: String!) {
  entity(url: $url) {
    iri
  }
}
```

## Notes

- Always use `rows` parameter to limit results and prevent timeouts
- For large datasets, use pagination with `page` and `rows`
- Use `dateModified` constraints for incremental syncs
- GTIN queries require GTIN-14 format (14 digits, left-padded with zeros)