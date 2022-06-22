using System.Collections.Generic;
using ${project_name};
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Test.Loader;

[TestClass]
public class UnionLoaderTests
{
    readonly UnionLoader loader = new(new List<ILoader>() { new PrimitiveLoader<int>(), new PrimitiveLoader<string>() });

    [TestMethod]
    public void TestLoad()
    {
        Assert.AreEqual("a", loader.Load("a", "", new LoadingOptions()));
        Assert.AreEqual(1, loader.Load(1, "", new LoadingOptions()));
    }

    [TestMethod]
    public void TestLoadFailure()
    {
        try
        {
            Assert.AreEqual(2.5, loader.Load(2.5, "", new LoadingOptions()));
        }
        catch (ValidationException e)
        {
            Assert.IsInstanceOfType(e, typeof(ValidationException));
            Assert.AreEqual("Failed to match union type:\n  Expected object with type of System.Int32 but got System.Double\n  Expected object with type of System.String but got System.Double", e.Message);
            return;
        }
        Assert.Fail("No ValidationException thrown");
    }
}
