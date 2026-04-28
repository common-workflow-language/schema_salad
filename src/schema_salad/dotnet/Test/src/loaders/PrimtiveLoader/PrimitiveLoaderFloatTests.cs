using ${project_name};
using Microsoft.VisualStudio.TestTools.UnitTesting;
namespace Test.Loader;

[TestClass]
public class PrimitiveLoaderFloatTests
{
    readonly PrimitiveLoader<float> primFloat = new();

    [TestMethod]
    public void TestMethod1()
    {
        Assert.AreEqual(1.0f, primFloat.Load(1.0f, "", new LoadingOptions(), ""));
        Assert.AreEqual(-1.0f, primFloat.Load(-1.0f, "", new LoadingOptions(), ""));
        Assert.AreEqual(0.0f, primFloat.Load(0.0f, "", new LoadingOptions(), ""));
    }

    [TestMethod]
    [ExpectedException(typeof(ValidationException))]
    public void TestExceptionStringEmpty()
    {
        primFloat.Load("", "", new LoadingOptions(), "");
    }

    [TestMethod]
    [ExpectedException(typeof(ValidationException))]
    public void TestExceptionStringNumber()
    {
        primFloat.Load("1.0f", "", new LoadingOptions(), "");
    }

    [TestMethod]
    [ExpectedException(typeof(ValidationException))]
    public void TestExceptionDouble()
    {
        primFloat.Load(2.5, "", new LoadingOptions(), "");
    }

    [TestMethod]
    [ExpectedException(typeof(ValidationException))]
    public void TestExceptionInt()
    {
        primFloat.Load(2, "", new LoadingOptions(), "");
    }

    [TestMethod]
    [ExpectedException(typeof(ValidationException))]
    public void TestExceptionNull()
    {
        primFloat.Load(null!, "", new LoadingOptions(), "");
    }
}
