using ${project_name};
using Microsoft.VisualStudio.TestTools.UnitTesting;
namespace Test.Loader;

[TestClass]
public class PrimitiveLoaderIntTests
{
    readonly PrimitiveLoader<int> primInt = new();

    [TestMethod]
    public void TestMethod1()
    {
        Assert.AreEqual(1, primInt.Load(1, "", new LoadingOptions(), ""));
        Assert.AreEqual(-1, primInt.Load(-1, "", new LoadingOptions(), ""));
        Assert.AreEqual(0, primInt.Load(0, "", new LoadingOptions(), ""));
    }

    [TestMethod]
    [ExpectedException(typeof(ValidationException))]
    public void TestExceptionStringEmpty()
    {
        primInt.Load("", "", new LoadingOptions(), "");
    }

    [TestMethod]
    [ExpectedException(typeof(ValidationException))]
    public void TestExceptionStringNumber()
    {
        primInt.Load("1", "", new LoadingOptions(), "");
    }

    [TestMethod]
    [ExpectedException(typeof(ValidationException))]
    public void TestExceptionDouble()
    {
        primInt.Load(2.5, "", new LoadingOptions(), "");
    }

    [TestMethod]
    [ExpectedException(typeof(ValidationException))]
    public void TestExceptionFloat()
    {
        primInt.Load(2.5f, "", new LoadingOptions(), "");
    }

    [TestMethod]
    [ExpectedException(typeof(ValidationException))]
    public void TestExceptionNull()
    {
        primInt.Load(null!, "", new LoadingOptions(), "");
    }
}
