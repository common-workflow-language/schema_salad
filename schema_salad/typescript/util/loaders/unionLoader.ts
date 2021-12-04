import { Loader, LoadingOptions, Saveable, ValidationException } from '../internal'

export class UnionLoader implements Loader {
  alternates: Loader[]

  constructor (alternates: Loader[]) {
    this.alternates = alternates
  }

  async load (doc: any, baseuri: string, loadingOptions: LoadingOptions, docRoot?: string): Promise<Saveable> {
    const errors: ValidationException[] = []
    for (const t of this.alternates) {
      try {
        return await t.load(doc, baseuri, loadingOptions)
      } catch (e) {
        if (e instanceof ValidationException) {
          errors.push(new ValidationException(`tried ${t.constructor.name} but`, [e]))
        }
      }
    }
    throw new ValidationException('', errors).withBullet('-')
  }
}
