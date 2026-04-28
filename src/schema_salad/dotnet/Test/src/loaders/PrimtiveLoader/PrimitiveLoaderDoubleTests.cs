using ${project_name};
using Microsoft.VisualStudio.TestTools.UnitTesting;
namespace Test.Loader;

[TestClass]
public class PrimitiveLoaderDoubleTests
{
    readonly PrimitiveLoader<double> primDouble = new();

    [TestMethod]
    public void TestMethod1()
    {
        Assert.AreEqual(1.0, primDouble.Load(1.0, "", new LoadingOptions(), ""));
        Assert.AreEqual(-1.0, primDouble.Load(-1.0, "", new LoadingOptions(), ""));
        Assert.AreEqual(0.0, primDouble.Load(0.0, "", new LoadingOptions(), ""));
    }

    [TestMethod]
    [ExpectedException(typeof(ValidationException))]
    public void TestExceptionStringEmpty()
    {
        primDouble.Load("", "", new LoadingOptions(), "");
    }

    [TestMethod]
    [ExpectedException(typeof(ValidationException))]
    public void TestExceptionStringNumber()
    {
        primDouble.Load("1.0", "", new LoadingOptions(), "");
    }

    [TestMethod]
    [ExpectedException(typeof(ValidationException))]
    public void TestExceptionFloat()
    {
        primDouble.Load(2.5f, "", new LoadingOptions(), "");
    }

    [TestMethod]
    [ExpectedException(typeof(ValidationException))]
    public void TestExceptionInt()
    {
        primDouble.Load(2, "", new LoadingOptions(), "");
    }

    [TestMethod]
    [ExpectedException(typeof(ValidationException))]
    public void TestExceptionNull()
    {
        primDouble.Load(null!, "", new LoadingOptions(), "");
    }
}
