import {Loader, loadField, LoadingOptions, _UnionLoader, ValidationException, TypeGuards, Dictionary} from '../Internal'

export class _MapLoader implements Loader {
  values: Loader[]
  container?: string

  constructor (values: Loader[], container?: string) {
    this.values = values
    this.container = container
  }

  async load (doc: any, baseuri: string, loadingOptions: LoadingOptions, docRoot?: string): Promise<any> {
    if (!TypeGuards.isDictionary(doc)) {
      throw new ValidationException('Expected a dict')
    }
    if (this.container !== undefined) {
      loadingOptions = new LoadingOptions({ copyFrom: loadingOptions, container: this.container })
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
