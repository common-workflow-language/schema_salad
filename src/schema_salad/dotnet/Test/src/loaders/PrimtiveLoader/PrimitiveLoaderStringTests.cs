using ${project_name};
using Microsoft.VisualStudio.TestTools.UnitTesting;
namespace Test.Loader;

[TestClass]
public class PrimitiveLoaderStringTests
{
    readonly PrimitiveLoader<string> primString = new();

    [TestMethod]
    public void TestMethod1()
    {
        Assert.AreEqual("", primString.Load("", "", new LoadingOptions(), ""));
        Assert.AreEqual("abcde", primString.Load("abcde", "", new LoadingOptions(), ""));
        Assert.AreEqual("1", primString.Load("1", "", new LoadingOptions(), ""));
    }

    [TestMethod]
    [ExpectedException(typeof(ValidationException))]
    public void TestExceptionInt()
    {
        primString.Load(2, "", new LoadingOptions(), "");
    }

    [TestMethod]
    [ExpectedException(typeof(ValidationException))]
    public void TestExceptionFloat()
    {
        primString.Load(2.0f, "", new LoadingOptions(), "");
    }

    [TestMethod]
    [ExpectedException(typeof(ValidationException))]
    public void TestExceptionDouble()
    {
        primString.Load(2.0, "", new LoadingOptions(), "");
    }

    [TestMethod]
    [ExpectedException(typeof(ValidationException))]
    public void TestExceptionNull()
    {
        primString.Load(null!, "", new LoadingOptions(), "");
    }
}
