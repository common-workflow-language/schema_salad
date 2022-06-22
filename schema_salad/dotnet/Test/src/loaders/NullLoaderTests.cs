using ${project_name};
using Microsoft.VisualStudio.TestTools.UnitTesting;
using OneOf.Types;
namespace Test.Loader;

[TestClass]
public class NullLoaderTests
{
    readonly NullLoader loader = new();

    [TestMethod]
    public void TestLoad()
    {
        Assert.AreEqual(typeof(None), loader.Load(null!, "", new LoadingOptions()).GetType());
    }

    [TestMethod]
    public void TestLoadFailure()
    {
        try
        {
            loader.Load(1, "", new LoadingOptions());
        }
        catch (ValidationException e)
        {
            Assert.IsInstanceOfType(e, typeof(ValidationException));
            Assert.AreEqual("Expected null", e.Message);
            return;
        }
        Assert.Fail("No ValidationException thrown");
    }
}
