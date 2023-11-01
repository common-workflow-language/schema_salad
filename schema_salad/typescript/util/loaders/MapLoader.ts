import {Loader, loadField, LoadingOptions, _UnionLoader, ValidationException, TypeGuards, Dictionary} from '../Internal'

export class _MapLoader implements Loader {
  values: Loader[]

  constructor (values: Loader[]) {
    this.values = values
  }

  async load (doc: any, baseuri: string, loadingOptions: LoadingOptions, docRoot?: string): Promise<any> {
    if (!TypeGuards.isDictionary(doc)) {
      throw new ValidationException('Expected a dict')
    }
    let r : Dictionary = {}
    const errors: ValidationException[] = []
    for (const key in doc) {
      try {
        r[key] = await loadField(doc[key], new _UnionLoader([this, ...this.values]), baseuri, loadingOptions)
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
