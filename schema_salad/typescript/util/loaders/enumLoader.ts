import { Loader, LoadingOptions, ValidationException } from '../internal'

export class EnumLoader implements Loader {
  symbols: string[]

  constructor (symbols: string[]) {
    this.symbols = symbols
  }

  async load (doc: string, baseuri: string, loadingOptions: LoadingOptions, docRoot?: string): Promise<any> {
    if (this.symbols.includes(doc)) {
      return doc
    } else {
      throw new ValidationException(`Expected one of ${this.symbols.toString()}`)
    }
  }
}
