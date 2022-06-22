using System;
using System.Collections.Generic;
using System.Linq;
using ${project_name};
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Test.Loader;

[TestClass]
public class EnumLoaderTests
{
    public class TestEnum : IEnumClass<TestEnum>
    {
        private string _Name;
        private static readonly List<TestEnum> members = new();

        public static readonly TestEnum A = new("A");
        public static readonly TestEnum B = new("B");
        public static readonly TestEnum C = new("C");
        public static readonly TestEnum D = new("D");
        public string Name
        {
            get { return _Name; }
            private set { _Name = value; }
        }

        public static IList<TestEnum> Members
        {
            get { return members; }
        }

        private TestEnum(string name)
        {
            _Name = name;
            members.Add(this);
        }

        public static TestEnum Parse(string toParse)
        {
            foreach (TestEnum s in Members)
            {
                if (toParse == s.Name)
                    return s;
            }
            throw new FormatException("Could not parse string.");
        }

        public static bool Contains(string value)
        {
            bool contains = false;
            foreach (TestEnum s in Members)
            {
                if (value == s.Name)
                {
                    contains = true;
                    return contains;
                }

            }
            return contains;
        }

        public override string ToString()
        {
            return _Name;
        }
        public static List<string> Symbols()
        {
            return members.Select(m => m.Name).ToList();
        }
    }

    readonly EnumLoader<TestEnum> loader = new();

    [TestMethod]
    public void TestLoad()
    {

        Assert.AreEqual(TestEnum.A, loader.Load("A", "", new LoadingOptions()));
    }

    [TestMethod]
    public void TestLoadFailure()
    {
        try
        {
            loader.Load("E", "", new LoadingOptions());
        }
        catch (ValidationException e)
        {
            Assert.IsInstanceOfType(e, typeof(ValidationException));
            Assert.AreEqual("Symbol not contained in TestEnum Enum, expected one of A, B, C, D", e.Message);
            return;
        }
        Assert.Fail("No ValidationException thrown");
    }
}
