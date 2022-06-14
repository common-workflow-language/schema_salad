using ${project_name};
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Test.Loader;

[TestClass]
public class AnyLoaderTests
{
    readonly AnyLoader loader = new();

    [TestMethod]
    public void TestLoad()
    {
        Assert.AreEqual("a", loader.Load("a", "", new LoadingOptions()));
        Assert.AreEqual('a', loader.Load('a', "", new LoadingOptions()));
        Assert.AreEqual(1, loader.Load(1, "", new LoadingOptions()));
        Assert.AreEqual(2.5, loader.Load(2.5, "", new LoadingOptions()));
        Assert.AreEqual(1.2f, loader.Load(1.2f, "", new LoadingOptions()));
    }

    [TestMethod]
    public void TestLoadFailure()
    {
        try
        {
            loader.Load(null!, "", new LoadingOptions());
        }
        catch (ValidationException e)
        {
            Assert.IsInstanceOfType(e, typeof(ValidationException));
            Assert.AreEqual("Expected non null", e.Message);
            return;
        }
        Assert.Fail("No ValidationException thrown");
    }
}
