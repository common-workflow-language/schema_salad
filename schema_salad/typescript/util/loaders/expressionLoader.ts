import { Loader, LoadingOptions, ValidationException } from '../internal'

export class ExpressionLoader implements Loader {
  items: string[]

  constructor (items: string[]) {
    this.items = items
  }

  async load (doc: any, baseuri: string, loadingOptions: LoadingOptions, docRoot?: string): Promise<any> {
    if (typeof doc !== 'string') {
      throw new ValidationException('Expected a str')
    }
    return doc
  }
}
