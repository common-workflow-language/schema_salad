using ${project_name};
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Test.Loader;

[TestClass]
public class NullLoaderTests
{
    readonly NullLoader loader = new();

    [TestMethod]
    public void TestLoad()
    {
        Assert.AreEqual(null!, loader.Load(null!, "", new LoadingOptions()));
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
