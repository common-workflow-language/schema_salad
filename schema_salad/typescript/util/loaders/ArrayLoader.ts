import { Loader, loadField, LoadingOptions, _UnionLoader, ValidationException } from '../Internal'

export class _ArrayLoader implements Loader {
  items: Loader[]
  flatten: boolean

  constructor (items: Loader[], flatten: boolean = true) {
    this.items = items
    this.flatten = flatten
  }

  async load (doc: any, baseuri: string, loadingOptions: LoadingOptions, docRoot?: string): Promise<any> {
    if (!Array.isArray(doc)) {
      throw new ValidationException('Expected a list')
    }
    let r: any[] = []
    const errors: ValidationException[] = []
    for (var val of doc) {
      try {
        const lf = await loadField(val, new _UnionLoader([this, ...this.items]), baseuri, loadingOptions)
        if (this.flatten && Array.isArray(lf)) {
          r = r.concat(lf)
        } else {
          r.push(lf)
        }
      } catch (e) {
        if (e instanceof ValidationException) {
          errors.push(e)
        } else {
          throw e
        }
      }
    }
    
    if (errors.length > 0) {
      throw new ValidationException('', errors)
    }
    return r
  }
}
